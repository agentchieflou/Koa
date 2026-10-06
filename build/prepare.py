#!/usr/bin/env python3
"""Turn this repository's sources into exactly what the build needs (build/README.md). Stdlib only.

    python build/prepare.py check                 the config is complete for the steps that need it
    python build/prepare.py lists                 build/out/FleetProvisionLists.zip: a flow that creates the five lists
    python build/prepare.py check-lists <file>    the list flow's Report, saved from its run: every list, column,
                                                  folder and the Owners-only lock are there
    python build/prepare.py flows                 build/out/FleetDecide.zip, and one FleetOutboxToLists (<UPN>).zip
                                                  per operator
    python build/prepare.py paste [N]             build/out/paste/: the app, one paste at a time, in order; with N,
                                                  paste N goes on the Windows clipboard
    python build/prepare.py canvas-out <path>     the app as Studio saved it (a .msapp, or a folder of .pa.yaml files)
                                                  copied back into powerapp/src

No MCP server and no agent plugin is involved: the build runs where they are blocked. Every flow is written twice:

- `build/out/<name>.zip`, a package for Power Automate's **My flows** > **Import** > **Import Package (Legacy)**,
  which the operator imports and connects in the browser;
- `build/out/<name>.json`, the same flow as `{name, definition, connectors, connectionRefsTemplate}`, for reading:
  `connectors` says which connection each connector needs and in which mode (`Embedded` = the operator's own
  connection, `Invoker` = the person running the app).

The flow definitions in `flows/` are the reviewed record; this script only applies the deploy-time differences a
flow outside a solution needs: the `_comment*` review notes removed, the solution environment variables replaced
by the values in `build/fleet.config.json`, and `authentication` dropped from action inputs (Power Automate injects
it on import). It never edits `flows/` or `powerapp/`, except `canvas-out`, which is the one command meant to write
`powerapp/src`.
"""
from __future__ import annotations
import argparse
import copy
import glob
import json
import os
import re
import subprocess
import sys
import uuid
import zipfile
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(BUILD, "out")
CONFIG = os.path.join(BUILD, "fleet.config.json")
CONTRACT = os.path.join(ROOT, "contract", "fleet-mobile.v1.schema.json")
DATA_README = os.path.join(ROOT, "data", "README.md")
FLOWS = os.path.join(ROOT, "flows")
SRC = os.path.join(ROOT, "powerapp", "src")

LISTS = ("FleetAttention", "FleetApprovals", "FleetDecisions", "FleetNotifications", "FleetHeartbeat")
#: SharePoint gives every list these columns, so the provisioning flow never creates them. `Title` is the key the
#: contract already uses; `Created` is SharePoint's own creation time (a Date and Time column), which the flow
#: cannot write and which stands in for the request's `created` (build/README.md, "The Created column").
BUILT_IN = {"Title", "Created"}
#: Multi-line beyond what data/README.md marks **multi**: `ApprovalsJson` can pass 255 characters (8 x 96-character
#: ids); flows/README.md "Verify on import" row 19 says to make it multi-line when it does, so it is made so here.
EXTRA_MULTI = {"FleetAttention": {"ApprovalsJson"}}
DESCRIPTIONS = {
    "FleetAttention": "FleetAgent: one row per repository, written by FleetOutboxToLists.",
    "FleetApprovals": "FleetAgent: one row per approval request, written by the flows.",
    "FleetDecisions": "FleetAgent: one row per phone decision or reply, written by FleetDecide and FleetOutboxToLists.",
    "FleetNotifications": "FleetAgent: the laptop's notifications, written by FleetOutboxToLists.",
    "FleetHeartbeat": "FleetAgent: each operator's laptop heartbeat, one row per operator (Title = the operator's UPN).",
}
#: Columns indexed on every list: every flow lookup filters on Title and Operator together, and an index keeps that
#: working past SharePoint's 5,000-item list view threshold (notifications grow with three operators).
INDEXED = ("Title", "Operator")
#: SharePoint's built-in role type for Full Control (SP.RoleType.Administrator).
FULL_CONTROL = 5

#: The solution environment variables the flows reference, and the config key that replaces each.
ENV_VARS = {
    "fleet_FleetSiteUrl": "siteUrl",
    "fleet_FleetLibrary": "library",
    "fleet_FleetAppId": "appId",
    "fleet_FleetOperator": "operators",          # one value per copy of FleetOutboxToLists: that copy's operator
}
#: What each step needs from build/fleet.config.json, and which step of build/steps/ supplies it.
NEEDS = {
    "lists": {"siteUrl": "01", "library": "01", "operators": "01"},
    "flows": {"siteUrl": "01", "library": "01", "operators": "01", "appId": "04"},
}
UPN = re.compile(r"[^@\s/\\#%:*?<>|\"]+@[^@\s/\\#%:*?<>|\"]+\.[^@\s/\\#%:*?<>|\"]+")
PARAM = re.compile(r"^@parameters\('(fleet_[A-Za-z]+) \(\1\)'\)$")
#: The same reference inside a larger expression, e.g. `@concat('/', parameters('fleet_FleetLibrary (...)'), ...)`.
EMBEDDED = re.compile(r"parameters\('(fleet_[A-Za-z]+) \(\1\)'\)")
#: `@concat(...)` of quoted literals only, which is what EMBEDDED leaves of the trigger's folder: folded to a string.
LITERAL_CONCAT = re.compile(r"^@concat\(((?:'(?:[^']|'')*'(?:, )?)+)\)$")
SP_API = "/providers/Microsoft.PowerApps/apis/shared_sharepointonline"
#: The connectors' names as the import page shows them, so the operator knows which connection to pick.
API_NAMES = {"shared_sharepointonline": "SharePoint", "shared_office365users": "Office 365 Users",
             "shared_powerappsnotificationv2": "Power Apps Notification (V2)",
             "shared_onedriveforbusiness": "OneDrive for Business"}
#: Fixed ids inside a package, so the same flow always imports under the same resource names.
PACKAGE_IDS = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/agentchieflou/Koa/build/package")


def _show(path: str) -> str:
    """A path for a log line: relative to the repository when it can be, absolute when it is on another drive
    (`os.path.relpath` raises across Windows drives)."""
    try:
        return os.path.relpath(path, ROOT)
    except ValueError:
        return path


class Refused(Exception):
    """A precondition the operator or an earlier step must supply; the message says which."""


# ------------------------------------------------------------------------------------ config


def load_config(path: str = CONFIG) -> dict:
    if not os.path.exists(path):
        raise Refused(f"{_show(path)} does not exist: copy build/fleet.config.example.json to it "
                      "and fill it in (build/steps/01-prerequisites.md)")
    with open(path, encoding="utf-8-sig") as f:
        cfg = json.load(f)
    cfg = {k: (v.strip() if isinstance(v, str) else v) for k, v in cfg.items() if not k.startswith("_")}
    if isinstance(cfg.get("operators"), list):
        cfg["operators"] = [str(op).strip().lower() for op in cfg["operators"] if str(op).strip()]
    return cfg


def require(cfg: dict, step: str, only: tuple[str, ...] = ()) -> None:
    missing = [f"{key} (build/steps/{n}-*.md)" for key, n in NEEDS[step].items()
               if (not only or key in only) and not cfg.get(key)]
    if missing:
        raise Refused(f"build/fleet.config.json is missing {', '.join(missing)}")
    for key, value in cfg.items():
        if isinstance(value, list) and any("contoso" in str(v).lower() for v in value):
            raise Refused(f"{key} still holds the example values: put this tenant's values in build/fleet.config.json")
        if isinstance(value, str) and "contoso" in value.lower():
            raise Refused(f"{key} is still the example value {value!r}: put this tenant's value in build/fleet.config.json")
    site = cfg.get("siteUrl", "")
    if site and not re.fullmatch(r"https://[A-Za-z0-9.-]+\.sharepoint\.(com|us|cn|de)/(sites|teams)/[^/?#]+", site):
        raise Refused(f"siteUrl {site!r} is not a SharePoint site address such as "
                      "https://contoso.sharepoint.com/sites/FleetAgent (no trailing slash, no page)")
    operators = cfg.get("operators")
    if operators is not None:
        if not isinstance(operators, list) or not 1 <= len(operators) <= 10:
            raise Refused("operators is a list of 1 to 10 UPNs: everyone whose fleet shares the site")
        for op in operators:
            if not UPN.fullmatch(op) or op != op.lower():
                raise Refused(f"operators: {op!r} is not a lowercase UPN such as you@contoso.com; it names that "
                              "operator's bridge folder, so it cannot hold / \\ # % : * ? < > | or a space")
        if len(set(operators)) != len(operators):
            raise Refused("operators lists someone twice")
    if cfg.get("library") and not re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,49}", cfg["library"]):
        raise Refused(f"library {cfg['library']!r} must be letters and digits, starting with a letter (FleetAgent)")
    if cfg.get("appId") and not re.fullmatch(r"[0-9a-fA-F-]{36}", cfg["appId"]):
        raise Refused(f"appId {cfg['appId']!r} is not the app's GUID (the app-id at the end of the Studio URL)")


# ------------------------------------------------------------------------------------ the lists


def multi_columns() -> dict[str, set[str]]:
    """The columns data/README.md marks **multi**, by list, plus EXTRA_MULTI."""
    out, table = {name: set(EXTRA_MULTI.get(name, set())) for name in LISTS}, None
    with open(DATA_README, encoding="utf-8") as f:
        for line in f:
            if m := re.match(r"^### `(Fleet[A-Za-z]+)`", line):
                table = m.group(1)
            elif table in out and (m := re.match(r"^\| `([A-Za-z0-9]+)` \| \*\*multi\*\* \|", line)):
                out[table].add(m.group(1))
    return out


def columns() -> dict[str, list[str]]:
    with open(CONTRACT, encoding="utf-8") as f:
        defs = json.load(f)["$defs"]
    return {name: list(defs[name]["properties"]) for name in LISTS}


def field_xml(name: str, multi: bool) -> str:
    """CAML for one column: single quotes only, so it sits inside a JSON string without escaping."""
    if multi:
        return (f"<Field Type='Note' Name='{name}' StaticName='{name}' DisplayName='{name}' NumLines='6' "
                f"RichText='FALSE' RichTextMode='Compatible' AppendOnly='FALSE' UnlimitedLengthInDocumentLibrary='FALSE' />")
    return f"<Field Type='Text' Name='{name}' StaticName='{name}' DisplayName='{name}' MaxLength='255' />"


def provisioning_spec(library: str = "FleetAgent") -> list[dict]:
    """The five lists (columns from the contract, indexed on Title and Operator) and the document library that holds
    one bridge folder per operator. Every entry is also a securable the flow locks to the site's Owners."""
    multi = multi_columns()
    spec = []
    for name, cols in columns().items():
        create = {"__metadata": {"type": "SP.List"}, "BaseTemplate": 100, "Title": name,
                  "Description": DESCRIPTIONS[name], "AllowContentTypes": True, "ContentTypesEnabled": False}
        spec.append({"list": name, "create": json.dumps(create, separators=(",", ":")), "columns": [
            {"name": col, "multi": col in multi[name],
             # 25 = AddToDefaultContentType (1) + AddFieldInternalNameHint (8) + AddFieldToDefaultView (16): the internal
             # name is exactly `col`, which is what every flow action and app formula addresses.
             "body": json.dumps({"parameters": {"__metadata": {"type": "SP.XmlSchemaFieldCreationInformation"},
                                                "SchemaXml": field_xml(col, col in multi[name]), "Options": 25}},
                                separators=(",", ":"))}
            for col in cols if col not in BUILT_IN],
            "indexed": [col for col in INDEXED if col in cols]})
    library_create = {"__metadata": {"type": "SP.List"}, "BaseTemplate": 101, "Title": library,
                      "Description": "FleetAgent: one bridge folder per operator, named by the operator's UPN."}
    spec.append({"list": library, "create": json.dumps(library_create, separators=(",", ":")), "columns": [],
                 "indexed": []})
    return spec


def _sp(method: str, uri: str, site: str, body: str | None = None, run_after: dict | None = None,
        verb: str | None = None) -> dict:
    """Send an HTTP request to SharePoint. `verb` is a MERGE or DELETE tunnelled through POST (X-HTTP-Method)."""
    headers = {"Accept": "application/json;odata=nometadata"}
    params = {"dataset": site, "parameters/method": method, "parameters/uri": uri, "parameters/headers": headers}
    if verb:
        headers["X-HTTP-Method"] = verb
        headers["IF-MATCH"] = "*"
    if body is not None:
        headers["Content-Type"] = "application/json;odata=verbose"
        params["parameters/body"] = body
    return {"type": "OpenApiConnection", "runAfter": run_after or {},
            "inputs": {"host": {"connectionName": "shared_sharepointonline", "operationId": "HttpRequest",
                                "apiId": SP_API}, "parameters": params}}


def _missing(collection: str, item: str) -> dict:
    return {"and": [{"not": {"contains": [f"@body('{collection}')", item]}}]}


def provisioning_flow(cfg: dict) -> dict:
    """A one-shot manual flow, safe to run again: it creates whatever is missing of the five lists, their columns
    and indexes, the bridge library and each operator's folder in it, then locks every one of them to the site's
    Owners group (Full Control, nothing else) and reads the permissions back as its evidence."""
    site, library, operators = cfg["siteUrl"], cfg["library"], cfg["operators"]
    each_list = "@items('For_each_list')?['list']"
    by_title = "_api/web/lists/getbytitle('@{items('For_each_list')?['list']}')"
    column_actions = {
        "Column_is_missing": {
            "type": "If", "runAfter": {},
            "expression": _missing("Select_field_names", "@items('For_each_column')?['name']"),
            "actions": {"Create_column": _sp("POST", f"{by_title}/fields/CreateFieldAsXml", site,
                                             body="@items('For_each_column')?['body']")},
            "else": {"actions": {}},
        },
    }
    list_actions = {
        "List_is_missing": {
            "type": "If", "runAfter": {},
            "expression": _missing("Select_list_titles", each_list),
            "actions": {"Create_list": _sp("POST", "_api/web/lists", site, body="@items('For_each_list')?['create']")},
            "else": {"actions": {}},
        },
        "Get_fields": _sp("GET", f"{by_title}/fields?$select=InternalName&$top=500", site,
                          run_after={"List_is_missing": ["Succeeded"]}),
        "Select_field_names": {"type": "Select", "runAfter": {"Get_fields": ["Succeeded"]},
                               "inputs": {"from": "@body('Get_fields')?['value']", "select": "@item()?['InternalName']"}},
        "For_each_column": {"type": "Foreach", "foreach": "@items('For_each_list')?['columns']",
                            "runAfter": {"Select_field_names": ["Succeeded"]},
                            "runtimeConfiguration": {"concurrency": {"repetitions": 1}}, "actions": column_actions},
        "For_each_index": {"type": "Foreach", "foreach": "@items('For_each_list')?['indexed']",
                           "runAfter": {"For_each_column": ["Succeeded"]},
                           "runtimeConfiguration": {"concurrency": {"repetitions": 1}}, "actions": {
                               "Index_column": _sp("POST", f"{by_title}/fields/getbyinternalnameortitle("
                                                           "'@{items('For_each_index')}')", site, verb="MERGE",
                                                   body='{"__metadata":{"type":"SP.Field"},"Indexed":true}')}},
    }
    lib = f"_api/web/lists/getbytitle('{library}')/rootfolder/folders"
    operator_actions = {
        "Folder_is_missing": {
            "type": "If", "runAfter": {},
            "expression": _missing("Select_folder_names", "@items('For_each_operator')"),
            "actions": {"Create_folder": _sp("POST", f"{lib}/add(url='@{{items('For_each_operator')}}')", site)},
            "else": {"actions": {}},
        },
    }
    securable = "_api/web/lists/getbytitle('@{items('For_each_securable')?['list']}')"
    owners, full = "@{body('Get_owner_group')?['Id']}", "@{body('Get_full_control')?['Id']}"
    assignment_actions = {
        "Not_the_owners": {
            "type": "If", "runAfter": {},
            "expression": {"and": [{"not": {"equals": ["@items('For_each_assignment')?['PrincipalId']",
                                                         "@body('Get_owner_group')?['Id']"]}}]},
            "actions": {"Remove_assignment": _sp(
                "POST", f"{securable}/roleassignments/getbyprincipalid(@{{items('For_each_assignment')?['PrincipalId']}})",
                site, verb="DELETE")},
            "else": {"actions": {}},
        },
    }
    lock_actions = {
        "Get_inheritance": _sp("GET", f"{securable}?$select=HasUniqueRoleAssignments", site),
        "Still_inherits": {
            "type": "If", "runAfter": {"Get_inheritance": ["Succeeded"]},
            "expression": {"and": [{"equals": ["@body('Get_inheritance')?['HasUniqueRoleAssignments']", False]}]},
            "actions": {"Break_inheritance": _sp(
                "POST", f"{securable}/breakroleinheritance(copyRoleAssignments=false,clearSubscopes=true)", site)},
            "else": {"actions": {}},
        },
        "Grant_owners": _sp("POST", f"{securable}/roleassignments/addroleassignment(principalid={owners},"
                                    f"roledefid={full})", site, run_after={"Still_inherits": ["Succeeded"]}),
        "Get_assignments": _sp("GET", f"{securable}/roleassignments?$select=PrincipalId", site,
                               run_after={"Grant_owners": ["Succeeded"]}),
        "For_each_assignment": {"type": "Foreach", "foreach": "@body('Get_assignments')?['value']",
                                "runAfter": {"Get_assignments": ["Succeeded"]},
                                "runtimeConfiguration": {"concurrency": {"repetitions": 1}},
                                "actions": assignment_actions},
        "Get_assignments_after": _sp("GET", f"{securable}/roleassignments?$select=PrincipalId", site,
                                     run_after={"For_each_assignment": ["Succeeded"]}),
        "Owners_only": {"type": "Compose", "runAfter": {"Get_assignments_after": ["Succeeded"]},
                        "inputs": {"list": "@items('For_each_securable')?['list']",
                                   "ownersOnly": "@and(equals(length(body('Get_assignments_after')?['value']), 1), "
                                                 "equals(first(body('Get_assignments_after')?['value'])?['PrincipalId'], "
                                                 "body('Get_owner_group')?['Id']))"}},
        "Get_fields_after": _sp("GET", f"{securable}/fields?$select=InternalName&$top=500", site,
                                run_after={"Owners_only": ["Succeeded"]}),
        "Select_fields_after": {"type": "Select", "runAfter": {"Get_fields_after": ["Succeeded"]},
                                "inputs": {"from": "@body('Get_fields_after')?['value']",
                                           "select": "@item()?['InternalName']"}},
        "Add_to_report": {"type": "AppendToArrayVariable", "runAfter": {"Select_fields_after": ["Succeeded"]},
                          "inputs": {"name": "Report", "value": {
                              "list": "@items('For_each_securable')?['list']",
                              "fields": "@body('Select_fields_after')",
                              "ownersOnly": "@outputs('Owners_only')?['ownersOnly']"}}},
    }
    definition = {
        "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {"$authentication": {"defaultValue": {}, "type": "SecureObject"},
                       "$connections": {"defaultValue": {}, "type": "Object"}},
        "triggers": {"manual": {"type": "Request", "kind": "Button",
                                "inputs": {"schema": {"type": "object", "properties": {}, "required": []}}}},
        "actions": {
            "Spec": {"type": "Compose", "runAfter": {}, "inputs": provisioning_spec(library)},
            "Initialize_report": {"type": "InitializeVariable", "runAfter": {"Spec": ["Succeeded"]},
                                  "inputs": {"variables": [{"name": "Report", "type": "array", "value": []}]}},
            "Get_lists": _sp("GET", "_api/web/lists?$select=Title&$top=5000", site,
                             run_after={"Initialize_report": ["Succeeded"]}),
            "Select_list_titles": {"type": "Select", "runAfter": {"Get_lists": ["Succeeded"]},
                                   "inputs": {"from": "@body('Get_lists')?['value']", "select": "@item()?['Title']"}},
            "For_each_list": {"type": "Foreach", "foreach": "@outputs('Spec')",
                              "runAfter": {"Select_list_titles": ["Succeeded"]},
                              "runtimeConfiguration": {"concurrency": {"repetitions": 1}}, "actions": list_actions},
            "Get_folders": _sp("GET", f"{lib}?$select=Name&$top=500", site, run_after={"For_each_list": ["Succeeded"]}),
            "Select_folder_names": {"type": "Select", "runAfter": {"Get_folders": ["Succeeded"]},
                                    "inputs": {"from": "@body('Get_folders')?['value']", "select": "@item()?['Name']"}},
            "For_each_operator": {"type": "Foreach", "foreach": list(operators),
                                  "runAfter": {"Select_folder_names": ["Succeeded"]},
                                  "runtimeConfiguration": {"concurrency": {"repetitions": 1}},
                                  "actions": operator_actions},
            "Get_owner_group": _sp("GET", "_api/web/associatedownergroup?$select=Id,Title", site,
                                   run_after={"For_each_operator": ["Succeeded"]}),
            "Get_full_control": _sp("GET", f"_api/web/roledefinitions/getbytype({FULL_CONTROL})?$select=Id,Name", site,
                                    run_after={"Get_owner_group": ["Succeeded"]}),
            "For_each_securable": {"type": "Foreach", "foreach": "@outputs('Spec')",
                                   "runAfter": {"Get_full_control": ["Succeeded"]},
                                   "runtimeConfiguration": {"concurrency": {"repetitions": 1}}, "actions": lock_actions},
            "Get_folders_after": _sp("GET", f"{lib}?$select=Name&$top=500", site,
                                     run_after={"For_each_securable": ["Succeeded"]}),
            "Select_folders_after": {"type": "Select", "runAfter": {"Get_folders_after": ["Succeeded"]},
                                     "inputs": {"from": "@body('Get_folders_after')?['value']",
                                                "select": "@item()?['Name']"}},
            "Report": {"type": "Compose", "runAfter": {"Select_folders_after": ["Succeeded"]},
                       "inputs": {"lists": "@variables('Report')", "folders": "@body('Select_folders_after')"}},
        },
        "description": "FleetAgent: creates the five lists, their columns and indexes, the bridge library and each "
                       "operator's folder, and locks all six to the site's Owners; safe to run again. Its last "
                       "action, Report, is what build/prepare.py check-lists reads.",
    }
    return _package("FleetProvisionLists", definition, {"shared_sharepointonline": "Embedded"})


def read_report(path: str) -> dict:
    """The Report action's output as the operator saved it from the run: the value itself, or Power Automate's
    raw outputs (`{"body": ...}`) around it."""
    if not os.path.exists(path):
        raise Refused(f"{_show(path)} does not exist: save the Report action's output there (build/steps/02-lists.md)")
    with open(path, encoding="utf-8-sig") as f:
        try:
            report = json.load(f)
        except json.JSONDecodeError as e:
            raise Refused(f"{_show(path)} is not JSON ({e}): copy the Report output whole, braces included")
    if isinstance(report, dict) and set(report) == {"body"}:
        report = report["body"]
    if not isinstance(report, dict) or not isinstance(report.get("lists"), list):
        raise Refused(f"{_show(path)} is not the Report action's output: it has no lists")
    return report


def check_lists(report: dict, cfg: dict) -> list[str]:
    """Every problem the Report shows, in words; empty when the five lists, their columns, the library, every
    operator's folder and the Owners-only lock are all there."""
    problems = []
    seen = {entry.get("list"): entry for entry in report["lists"] if isinstance(entry, dict)}
    for entry in provisioning_spec(cfg["library"]):
        name = entry["list"]
        got = seen.get(name)
        if got is None:
            problems.append(f"{name}: not in the report; the run did not reach it")
            continue
        missing = [c["name"] for c in entry["columns"] if c["name"] not in set(got.get("fields") or [])]
        if missing:
            problems.append(f"{name}: missing {', '.join(missing)}")
        if got.get("ownersOnly") is not True:
            problems.append(f"{name}: not Owners-only; someone besides the site's Owners group can still read it")
    folders = {str(f).lower() for f in report.get("folders") or []}
    for op in cfg["operators"]:
        if op not in folders:
            problems.append(f"{cfg['library']}: no folder {op}")
    return problems


# ------------------------------------------------------------------------------------ the two flows


def _strip_comments(node):
    if isinstance(node, dict):
        return {k: _strip_comments(v) for k, v in node.items() if not k.startswith("_comment")}
    if isinstance(node, list):
        return [_strip_comments(v) for v in node]
    return node


def _deploy(node, values: dict, used: set):
    """Environment variables to literals; `authentication` out of action and trigger inputs."""
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k == "authentication" and v == "@parameters('$authentication')":
                continue
            out[k] = _deploy(v, values, used)
        return out
    if isinstance(node, list):
        return [_deploy(v, values, used) for v in node]
    if isinstance(node, str) and (m := PARAM.match(node)):
        used.add(m.group(1))
        return values[m.group(1)]
    if isinstance(node, str) and node.startswith("@") and EMBEDDED.search(node):
        def literal(m):
            used.add(m.group(1))
            return "'" + values[m.group(1)].replace("'", "''") + "'"
        folded = EMBEDDED.sub(literal, node)
        if m := LITERAL_CONCAT.match(folded):
            return "".join(part.replace("''", "'") for part in re.findall(r"'((?:[^']|'')*)'", m.group(1)))
        return folded
    return node


def outbox_name(operator: str) -> str:
    """Each operator's copy of FleetOutboxToLists, by name: one copy per operator keeps each copy's requests inside
    the per-flow daily limit, and under that operator's own limit once its primary owner is changed to them."""
    return f"FleetOutboxToLists ({operator})"


def deploy_flow(name: str, cfg: dict, operator: str = "") -> dict:
    with open(os.path.join(FLOWS, f"{name}.definition.json"), encoding="utf-8") as f:
        source = _strip_comments(json.load(f))["properties"]
    values = {var: cfg.get(key, "") for var, key in ENV_VARS.items() if key != "operators"}
    values["fleet_FleetOperator"] = operator
    used: set = set()
    definition = _deploy(copy.deepcopy(source["definition"]), values, used)
    definition["parameters"] = {k: v for k, v in definition["parameters"].items() if not k.startswith("fleet_")}
    unset = sorted(f"{ENV_VARS[v]}" for v in used if not values[v])
    if unset:
        raise Refused(f"{name} needs {', '.join(unset)} in build/fleet.config.json")
    modes = {key: {"embedded": "Embedded", "invoker": "Invoker"}[ref["runtimeSource"]]
             for key, ref in source["connectionReferences"].items()}
    return _package(outbox_name(operator) if operator else name, definition, modes)


def _package(name: str, definition: dict, modes: dict) -> dict:
    hosts = {m.group(1) for m in re.finditer(r'"connectionName": "([^"]+)"', json.dumps(definition))}
    assert hosts == set(modes), f"{name}: connections {sorted(hosts)} but references {sorted(modes)}"
    return {"name": name, "definition": definition, "connectors": modes,
            "connectionRefsTemplate": {key: {"connectionName": "<picked when the package is imported>", "source": mode,
                                             "id": f"/providers/Microsoft.PowerApps/apis/{key}", "tier": "NotSpecified"}
                                       for key, mode in modes.items()}}


def import_package(package: dict, created: str | None = None) -> dict[str, bytes]:
    """The files of a package for **Import Package (Legacy)**, laid out as Power Automate exports one: a root
    manifest naming the flow and, per connector, the API and a connection the operator picks while importing."""
    name = package["name"]
    ids = uuid.uuid5(PACKAGE_IDS, name)
    flow, flow_name = str(uuid.uuid5(ids, "resource/flow")), str(uuid.uuid5(ids, "flow"))
    api = {key: str(uuid.uuid5(ids, f"resource/api/{key}")) for key in package["connectors"]}
    connection = {key: str(uuid.uuid5(ids, f"resource/connection/{key}")) for key in package["connectors"]}
    resources = {flow: {"type": "Microsoft.Flow/flows", "suggestedCreationType": "New",
                        "creationType": "Existing, New, Update", "details": {"displayName": name},
                        "configurableBy": "User", "hierarchy": "Root",
                        "dependsOn": [r for key in package["connectors"] for r in (api[key], connection[key])]}}
    for key in package["connectors"]:
        title = API_NAMES.get(key, key)
        resources[api[key]] = {"id": f"/providers/Microsoft.PowerApps/apis/{key}", "name": key,
                               "type": "Microsoft.PowerApps/apis", "suggestedCreationType": "Existing",
                               "details": {"displayName": title}, "configurableBy": "System", "hierarchy": "Child",
                               "dependsOn": []}
        resources[connection[key]] = {"type": "Microsoft.PowerApps/apis/connections", "suggestedCreationType": "Existing",
                                      "creationType": "Existing", "details": {"displayName": title},
                                      "configurableBy": "User", "hierarchy": "Child", "dependsOn": [api[key]]}
    created = created or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.0000000Z")
    manifest = {"schema": "1.0", "details": {"displayName": name, "description": package["definition"].get("description", ""),
                                             "createdTime": created, "packageTelemetryId": str(uuid.uuid5(ids, "telemetry")),
                                             "creator": "N/A", "sourceEnvironment": ""},
                "resources": resources}
    definition = {"name": flow_name, "id": f"/providers/Microsoft.Flow/flows/{flow_name}", "type": "Microsoft.Flow/flows",
                  "properties": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_logicflows", "displayName": name,
                                 "definition": package["definition"],
                                 "connectionReferences": {key: {"connectionName": key, "source": mode,
                                                                "id": f"/providers/Microsoft.PowerApps/apis/{key}",
                                                                "tier": "NotSpecified"}
                                                          for key, mode in package["connectors"].items()},
                                 "flowFailureAlertSubscribed": False}}
    dump = lambda data: json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    base = f"Microsoft.Flow/flows/{flow}/"
    return {"manifest.json": dump(manifest),
            "Microsoft.Flow/flows/manifest.json": dump({"packageSchemaVersion": "1.0", "flowAssets": {"assetPaths": [flow]}}),
            base + "definition.json": dump(definition),
            base + "apisMap.json": dump(api),
            base + "connectionsMap.json": dump(connection)}


def write_out(package: dict, out: str = OUT) -> list[str]:
    """`<name>.zip` to import and `<name>.json` to read, side by side."""
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, f"{package['name']}.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(package, f, indent=2, ensure_ascii=False)
        f.write("\n")
    archive = os.path.join(out, f"{package['name']}.zip")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for rel, data in import_package(package).items():
            z.writestr(rel, data)
    return [archive, path]


# ------------------------------------------------------------------------------------ the app


#: The App object's properties, in the order they are typed into Studio's formula bar (code view cannot paste the
#: App object). Formulas first, so the screens' named formulas resolve; StartScreen last, because it names screens.
APP_PROPERTIES = ("Formulas", "OnError", "BackEnabled", "StartScreen")
#: The screens in the order that leaves the fewest names unresolved while pasting (README.md, step 5).
PASTE_SCREENS = ("SettingsScreen", "ReplyScreen", "DecideScreen", "ApprovalScreen", "AgentScreen", "HomeScreen")


def _screens_order() -> list[str]:
    with open(os.path.join(SRC, "_EditorState.pa.yaml"), encoding="utf-8") as f:
        text = f.read()
    block = text.split("ScreensOrder:", 1)[1].split("ComponentDefinitionsOrder:", 1)[0]
    return re.findall(r"^\s*-\s*(\S+)\s*$", block, re.M)


def _components_order() -> list[str]:
    with open(os.path.join(SRC, "_EditorState.pa.yaml"), encoding="utf-8") as f:
        block = f.read().split("ComponentDefinitionsOrder:", 1)[1]
    return re.findall(r"^\s*-\s*(\S+)\s*$", block, re.M)


def app_properties() -> dict[str, str]:
    """Each App property as it goes into the formula bar: the formula without its leading `=`."""
    with open(os.path.join(SRC, "App.pa.yaml"), encoding="utf-8") as f:
        lines = f.read().split("\n")
    out, name, block = {}, None, []
    for line in lines[2:]:                                    # after `App:` and `  Properties:`
        if m := re.match(r"^    ([A-Za-z]+): (.*)$", line):
            if name:
                out[name] = "\n".join(block).rstrip("\n")
            name, value = m.group(1), m.group(2)
            block = [] if value == "|-" else [value]
        elif name and (line.startswith("      ") or not line.strip()):
            block.append(line[6:])
    if name:
        out[name] = "\n".join(block).rstrip("\n")
    missing = [p for p in APP_PROPERTIES if p not in out]
    if missing:
        raise Refused(f"powerapp/src/App.pa.yaml has no {', '.join(missing)}")
    return {p: out[p][1:] if out[p].startswith("=") else out[p] for p in APP_PROPERTIES}


def paste_plan() -> list[dict]:
    """Everything the operator pastes into Studio, in order: the components, the screens, then the App object's
    properties. Each item is one paste of one whole file."""
    plan = []
    for name in _components_order():
        plan.append({"name": name, "source": os.path.join(SRC, "Components", f"{name}.pa.yaml"), "file": f"{name}.pa.yaml",
                     "where": "Tree view > Components tab > right-click the empty area > Paste code"})
    if sorted(PASTE_SCREENS) != sorted(_screens_order()):
        raise Refused("PASTE_SCREENS no longer names the app's screens: update it from powerapp/src/_EditorState.pa.yaml")
    for name in PASTE_SCREENS:
        plan.append({"name": name, "source": os.path.join(SRC, "Screens", f"{name}.pa.yaml"), "file": f"{name}.pa.yaml",
                     "where": "Tree view > Screens tab > right-click the empty area > Paste code"})
    for prop, text in app_properties().items():
        plan.append({"name": f"App.{prop}", "text": text, "file": f"App.{prop}.txt",
                     "where": f"Tree view > select App > property list: {prop} > click into the formula bar, "
                              "select all, paste"})
    for n, item in enumerate(plan, 1):
        item["n"] = n
        item["file"] = f"{n:02d}-{item['file']}"
    return plan


def write_paste(out: str | None = None) -> list[dict]:
    out = out or os.path.join(OUT, "paste")
    os.makedirs(out, exist_ok=True)
    plan = paste_plan()
    for item in plan:
        if "source" in item:
            with open(item["source"], "rb") as f:
                data = f.read()
        else:
            data = (item["text"] + "\n").encode("utf-8")
        item["path"] = os.path.join(out, item["file"])
        with open(item["path"], "wb") as f:
            f.write(data)
    return plan


def to_clipboard(path: str) -> bool:
    """Put a file's text on the Windows clipboard (PowerShell's Set-Clipboard keeps it Unicode); False elsewhere."""
    if os.name != "nt":
        return False
    command = "Set-Clipboard -Value ([System.IO.File]::ReadAllText($env:FLEET_PASTE))"
    done = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                          env={**os.environ, "FLEET_PASTE": path}, capture_output=True)
    return done.returncode == 0


def _from_msapp(path: str) -> dict[str, bytes]:
    """The `.pa.yaml` files Studio keeps inside a saved `.msapp`, under its `Src` folder, keyed as canvas_out
    expects them (screens at the root, components under `Components/`)."""
    out = {}
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            parts = info.filename.replace("\\", "/").split("/")
            if len(parts) < 2 or parts[0].lower() != "src" or not parts[-1].endswith(".pa.yaml"):
                continue
            rel = "/".join(parts[1:])
            if parts[1].lower() in ("component", "components"):
                rel = "Components/" + "/".join(parts[2:])
            out[rel] = z.read(info)
    if "App.pa.yaml" not in out:
        raise Refused(f"{_show(path)} has no Src/App.pa.yaml: save the app in Studio first, then download it again "
                      "(build/steps/07-finish.md)")
    return out


def _from_folder(workdir: str) -> dict[str, bytes]:
    out = {}
    for path in glob.glob(os.path.join(workdir, "**", "*.pa.yaml"), recursive=True):
        rel = os.path.relpath(path, workdir).replace(os.sep, "/")
        if rel.lower().startswith("src/"):
            rel = rel[4:]
        if rel.lower().startswith("component/"):
            rel = "Components/" + rel.split("/", 1)[1]
        with open(path, "rb") as f:
            out[rel] = f.read()
    if "App.pa.yaml" not in out:
        raise Refused(f"{_show(workdir)} has no App.pa.yaml: give the saved .msapp, or the folder holding its Src files")
    return out


def canvas_out(source: str) -> list[str]:
    """Copy the app as Studio saved it back over powerapp/src, so the repository mirrors what Studio holds."""
    source = os.path.abspath(source)
    files = _from_msapp(source) if os.path.isfile(source) else _from_folder(source)
    log = []
    for rel, raw in sorted(files.items()):
        if rel.startswith("Components/"):
            dest = os.path.join(SRC, "Components", rel.split("/", 1)[1])
        elif rel in ("App.pa.yaml", "_EditorState.pa.yaml"):
            dest = os.path.join(SRC, rel)
        elif "/" not in rel:
            dest = os.path.join(SRC, "Screens", rel)
        else:
            raise Refused(f"{rel}: an unexpected folder in the saved app")
        raw = raw.replace(b"\r\n", b"\n")
        with open(dest, "wb") as f:
            f.write(raw if raw.endswith(b"\n") else raw + b"\n")
        log.append(f"{rel} -> {_show(dest)}")
    return log


# ------------------------------------------------------------------------------------ main


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("lists")
    sub.add_parser("check-lists").add_argument("report")
    sub.add_parser("flows")
    sub.add_parser("paste").add_argument("n", nargs="?", type=int)
    sub.add_parser("canvas-out").add_argument("source")
    args = p.parse_args(argv)
    try:
        if args.cmd == "check":
            cfg = load_config()
            for step in NEEDS:
                try:
                    require(cfg, step)
                    print(f"{step}: ready")
                except Refused as e:
                    print(f"{step}: {e}")
        elif args.cmd == "lists":
            cfg = load_config()
            require(cfg, "lists")
            print("\n".join(write_out(provisioning_flow(cfg))))
        elif args.cmd == "check-lists":
            cfg = load_config()
            require(cfg, "lists")
            problems = check_lists(read_report(args.report), cfg)
            print("\n".join(problems) if problems else
                  f"lists: ready ({len(LISTS)} lists and {cfg['library']}, every column, every operator's folder, "
                  "Owners only)")
            return 1 if problems else 0
        elif args.cmd == "flows":
            cfg = load_config()
            require(cfg, "flows", only=("siteUrl", "library"))
            print("\n".join(write_out(deploy_flow("FleetDecide", cfg))))
            if cfg.get("appId"):
                require(cfg, "flows")
                for operator in cfg["operators"]:
                    print("\n".join(write_out(deploy_flow("FleetOutboxToLists", cfg, operator))))
            else:
                print("FleetOutboxToLists: waits for appId (build/steps/04-app-shell.md)")
        elif args.cmd == "paste":
            plan = write_paste()
            if args.n is None:
                for item in plan:
                    print(f"{item['n']:2d}. {item['name']:<16} {item['where']}")
                print(f"files: {_show(os.path.dirname(plan[0]['path']))}")
            else:
                if not 1 <= args.n <= len(plan):
                    raise Refused(f"paste {args.n}: there are {len(plan)} pastes, 1 to {len(plan)}")
                item = plan[args.n - 1]
                where = "on the clipboard" if to_clipboard(item["path"]) else f"in {_show(item['path'])}: open it, copy all"
                print(f"paste {item['n']} of {len(plan)}, {item['name']}: {where}. In Studio: {item['where']}.")
        elif args.cmd == "canvas-out":
            print("\n".join(canvas_out(args.source)))
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
