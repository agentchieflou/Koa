#!/usr/bin/env python3
"""Turn this repository's sources into exactly what the Copilot build needs (build/README.md). Stdlib only.

    python build/prepare.py check                 the config is complete for the steps that need it
    python build/prepare.py lists                 build/out/FleetProvisionLists.json: a flow that creates the five lists
    python build/prepare.py flows                 build/out/FleetDecide.json and build/out/FleetOutboxToLists.json
    python build/prepare.py canvas-in  <workdir>  copy powerapp/src into the Canvas Authoring MCP working directory
    python build/prepare.py canvas-out <workdir>  copy a synced working directory back into powerapp/src

Every flow file it writes is `{name, definition, connectors, connectionRefsTemplate}`: `definition` is what the
FlowAgent MCP tool `create_flow` takes, `connectors` says which connection each connector needs and in which mode
(`Embedded` = the operator's own connection, `Invoker` = the person running the app), and the template is the
`connectionRefs` argument with the connection names left for `pick_or_create_connection` to fill.

The flow definitions in `flows/` are the reviewed record; this script only applies the deploy-time differences a
flow outside a solution needs: the `_comment*` review notes removed, the solution environment variables replaced
by the values in `build/fleet.config.json`, and `authentication` dropped from action inputs (Power Automate injects
it; FlowAgent's validator refuses it). It never edits `flows/` or `powerapp/`, except `canvas-out`, which is the one
command meant to write `powerapp/src`.
"""
from __future__ import annotations
import argparse
import copy
import glob
import json
import os
import re
import shutil
import sys

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
    "FleetHeartbeat": "FleetAgent: the laptop's heartbeat, one row (Title = laptop).",
}

#: The solution environment variables the flows reference, and the config key that replaces each.
ENV_VARS = {
    "fleet_FleetSiteUrl": "siteUrl",
    "fleet_FleetOutboxFolderId": "outboxFolderId",
    "fleet_FleetInboxFolderPath": "inboxFolderPath",
    "fleet_FleetAppId": "appId",
    "fleet_FleetOperatorEmail": "operator",
}
#: What each step needs from build/fleet.config.json, and which step of build/steps/ supplies it.
NEEDS = {
    "lists": {"siteUrl": "01"},
    "flows": {"siteUrl": "01", "operator": "01", "inboxFolderPath": "01", "outboxFolderId": "05", "appId": "04"},
}
PARAM = re.compile(r"^@parameters\('(fleet_[A-Za-z]+) \(\1\)'\)$")
SP_API = "/providers/Microsoft.PowerApps/apis/shared_sharepointonline"


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
    return {k: (v.strip() if isinstance(v, str) else v) for k, v in cfg.items() if not k.startswith("_")}


def require(cfg: dict, step: str, only: tuple[str, ...] = ()) -> None:
    missing = [f"{key} (build/steps/{n}-*.md)" for key, n in NEEDS[step].items()
               if (not only or key in only) and not cfg.get(key)]
    if missing:
        raise Refused(f"build/fleet.config.json is missing {', '.join(missing)}")
    for key, value in cfg.items():
        if isinstance(value, str) and "contoso" in value.lower():
            raise Refused(f"{key} is still the example value {value!r}: put this tenant's value in build/fleet.config.json")
    site = cfg.get("siteUrl", "")
    if site and not re.fullmatch(r"https://[A-Za-z0-9.-]+\.sharepoint\.(com|us|cn|de)/(sites|teams)/[^/?#]+", site):
        raise Refused(f"siteUrl {site!r} is not a SharePoint site address such as "
                      "https://contoso.sharepoint.com/sites/FleetAgent (no trailing slash, no page)")
    if cfg.get("operator") and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", cfg["operator"]):
        raise Refused(f"operator {cfg['operator']!r} is not a UPN such as you@contoso.com")
    if cfg.get("inboxFolderPath") and not cfg["inboxFolderPath"].startswith("/"):
        raise Refused("inboxFolderPath is a OneDrive path from the root, such as /FleetAgent/inbox")
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


def provisioning_spec() -> list[dict]:
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
            for col in cols if col not in BUILT_IN]})
    return spec


def _sp(method: str, uri: str, site: str, body: str | None = None, run_after: dict | None = None) -> dict:
    headers = {"Accept": "application/json;odata=nometadata"}
    params = {"dataset": site, "parameters/method": method, "parameters/uri": uri, "parameters/headers": headers}
    if body is not None:
        headers["Content-Type"] = "application/json;odata=verbose"
        params["parameters/body"] = body
    return {"type": "OpenApiConnection", "runAfter": run_after or {},
            "inputs": {"host": {"connectionName": "shared_sharepointonline", "operationId": "HttpRequest",
                                "apiId": SP_API}, "parameters": params}}


def provisioning_flow(cfg: dict) -> dict:
    """A one-shot manual flow that creates whatever of the five lists and their columns is missing, and leaves
    everything that exists alone, so running it twice changes nothing."""
    site = cfg["siteUrl"]
    each_list = "@items('For_each_list')?['list']"
    by_title = "_api/web/lists/getbytitle('@{items('For_each_list')?['list']}')"
    column_actions = {
        "Column_is_missing": {
            "type": "If", "runAfter": {},
            "expression": {"and": [{"not": {"contains": ["@body('Select_field_names')", "@items('For_each_column')?['name']"]}}]},
            "actions": {"Create_column": _sp("POST", f"{by_title}/fields/CreateFieldAsXml", site,
                                             body="@items('For_each_column')?['body']")},
            "else": {"actions": {}},
        },
    }
    list_actions = {
        "List_is_missing": {
            "type": "If", "runAfter": {},
            "expression": {"and": [{"not": {"contains": ["@body('Select_list_titles')", each_list]}}]},
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
    }
    definition = {
        "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {"$authentication": {"defaultValue": {}, "type": "SecureObject"},
                       "$connections": {"defaultValue": {}, "type": "Object"}},
        "triggers": {"manual": {"type": "Request", "kind": "Button",
                                "inputs": {"schema": {"type": "object", "properties": {}, "required": []}}}},
        "actions": {
            "Spec": {"type": "Compose", "runAfter": {}, "inputs": provisioning_spec()},
            "Get_lists": _sp("GET", "_api/web/lists?$select=Title&$top=5000", site, run_after={"Spec": ["Succeeded"]}),
            "Select_list_titles": {"type": "Select", "runAfter": {"Get_lists": ["Succeeded"]},
                                   "inputs": {"from": "@body('Get_lists')?['value']", "select": "@item()?['Title']"}},
            "For_each_list": {"type": "Foreach", "foreach": "@outputs('Spec')",
                              "runAfter": {"Select_list_titles": ["Succeeded"]},
                              "runtimeConfiguration": {"concurrency": {"repetitions": 1}}, "actions": list_actions},
        },
        "description": "FleetAgent: creates the five lists and their columns on the site; safe to run again.",
    }
    return _package("FleetProvisionLists", definition, {"shared_sharepointonline": "Embedded"})


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
    return node


def deploy_flow(name: str, cfg: dict) -> dict:
    with open(os.path.join(FLOWS, f"{name}.definition.json"), encoding="utf-8") as f:
        source = _strip_comments(json.load(f))["properties"]
    values = {var: cfg.get(key, "") for var, key in ENV_VARS.items()}
    used: set = set()
    definition = _deploy(copy.deepcopy(source["definition"]), values, used)
    definition["parameters"] = {k: v for k, v in definition["parameters"].items() if not k.startswith("fleet_")}
    unset = sorted(f"{ENV_VARS[v]}" for v in used if not values[v])
    if unset:
        raise Refused(f"{name} needs {', '.join(unset)} in build/fleet.config.json")
    modes = {key: {"embedded": "Embedded", "invoker": "Invoker"}[ref["runtimeSource"]]
             for key, ref in source["connectionReferences"].items()}
    return _package(name, definition, modes)


def _package(name: str, definition: dict, modes: dict) -> dict:
    hosts = {m.group(1) for m in re.finditer(r'"connectionName": "([^"]+)"', json.dumps(definition))}
    assert hosts == set(modes), f"{name}: connections {sorted(hosts)} but references {sorted(modes)}"
    return {"name": name, "definition": definition, "connectors": modes,
            "connectionRefsTemplate": {key: {"connectionName": "<pick_or_create_connection>", "source": mode,
                                             "id": f"/providers/Microsoft.PowerApps/apis/{key}", "tier": "NotSpecified"}
                                       for key, mode in modes.items()}}


def write_out(package: dict) -> str:
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"{package['name']}.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(package, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return path


# ------------------------------------------------------------------------------------ the app


def _source_files() -> dict[str, str]:
    """Working-directory name -> repository path: screens flat at the root, components under Components/, as the
    Canvas Authoring MCP server lays an app out (and as Studio's Src folder does)."""
    out = {"App.pa.yaml": os.path.join(SRC, "App.pa.yaml"), "_EditorState.pa.yaml": os.path.join(SRC, "_EditorState.pa.yaml")}
    for path in sorted(glob.glob(os.path.join(SRC, "Screens", "*.pa.yaml"))):
        out[os.path.basename(path)] = path
    for path in sorted(glob.glob(os.path.join(SRC, "Components", "*.pa.yaml"))):
        out["Components/" + os.path.basename(path)] = path
    return out


def _yaml_files(workdir: str) -> list[str]:
    found = []
    for path in glob.glob(os.path.join(workdir, "**", "*"), recursive=True):
        if os.path.isfile(path):
            rel = os.path.relpath(path, workdir).replace(os.sep, "/")
            if not rel.endswith(".pa.yaml"):
                raise Refused(f"{workdir} holds {rel}: the MCP working directory must hold .pa.yaml files only")
            found.append(rel)
    return sorted(found)


def _screens_order() -> list[str]:
    with open(os.path.join(SRC, "_EditorState.pa.yaml"), encoding="utf-8") as f:
        text = f.read()
    block = text.split("ScreensOrder:", 1)[1].split("ComponentDefinitionsOrder:", 1)[0]
    return re.findall(r"^\s*-\s*(\S+)\s*$", block, re.M)


def canvas_in(workdir: str) -> list[str]:
    """Put the repository's app into a working directory `sync_canvas` filled from the blank app."""
    workdir = os.path.abspath(workdir)
    if os.path.abspath(ROOT) == workdir:
        raise Refused("never use the repository root as the MCP working directory; use build/out/canvas/FleetAgent")
    present = _yaml_files(workdir) if os.path.isdir(workdir) else []
    if "App.pa.yaml" not in present:
        raise Refused(f"{workdir} has no App.pa.yaml: run sync_canvas into it first (build/steps/06-app.md)")
    log = []
    keep = set(_screens_order())
    for rel in present:
        name = rel[:-len(".pa.yaml")]
        if "/" not in rel and name not in keep and name not in ("App", "_EditorState"):
            os.remove(os.path.join(workdir, rel))                 # the blank app's Screen1
            log.append(f"removed {rel} (a screen the app does not have)")
    for rel, src in _source_files().items():
        dest = os.path.join(workdir, *rel.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(src, dest)
        log.append(f"wrote {rel}")
    return log


def canvas_out(workdir: str) -> list[str]:
    """Copy a synced working directory back over powerapp/src, so the repository mirrors what Studio holds."""
    workdir = os.path.abspath(workdir)
    present = _yaml_files(workdir)
    if "App.pa.yaml" not in present:
        raise Refused(f"{workdir} has no App.pa.yaml: sync_canvas into an empty directory first")
    log = []
    for rel in present:
        if rel.startswith("Components/"):
            dest = os.path.join(SRC, "Components", rel.split("/", 1)[1])
        elif rel in ("App.pa.yaml", "_EditorState.pa.yaml"):
            dest = os.path.join(SRC, rel)
        elif "/" not in rel:
            dest = os.path.join(SRC, "Screens", rel)
        else:
            raise Refused(f"{rel}: an unexpected folder in the synced app")
        with open(os.path.join(workdir, rel), "rb") as f:
            raw = f.read().replace(b"\r\n", b"\n")
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
    sub.add_parser("flows")
    for name in ("canvas-in", "canvas-out"):
        sub.add_parser(name).add_argument("workdir")
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
            print(write_out(provisioning_flow(cfg)))
        elif args.cmd == "flows":
            cfg = load_config()
            require(cfg, "flows", only=("siteUrl", "operator", "inboxFolderPath"))
            print(write_out(deploy_flow("FleetDecide", cfg)))
            if cfg.get("outboxFolderId") and cfg.get("appId"):
                print(write_out(deploy_flow("FleetOutboxToLists", cfg)))
            else:
                print("FleetOutboxToLists: waits for appId (build/steps/04-app-shell.md) and outboxFolderId (build/steps/05-outbox-flow.md)")
        elif args.cmd == "canvas-in":
            print("\n".join(canvas_in(args.workdir)))
        elif args.cmd == "canvas-out":
            print("\n".join(canvas_out(args.workdir)))
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
