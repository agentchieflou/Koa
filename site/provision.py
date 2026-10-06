#!/usr/bin/env python3
"""Turn the site's list spec into what SharePoint takes (site/README.md, step 2). Stdlib only.

    python site/provision.py check                    the spec is complete and consistent
    python site/provision.py scripts                  site/out/scripts/NN-<List>.json: one site script per list
    python site/provision.py flow    --site <url>     site/out/CzarsProvisionSite.json: a one-shot flow for FlowAgent
    python site/provision.py console --site <url>     site/out/provision.console.js: the same, pasted in the browser
    python site/provision.py docs                     rewrite site/LISTS.md from the spec

`site/lists.json` is the record: every list, column, view and starter row. `site/formatting/*.json` are the column,
gallery and row formatters it names. Each list becomes one site script (`createSPList` with its columns, formatters
and views as subactions), applied in order by SharePoint's `ExecuteTemplateScript` endpoint, the one PnP's
`Invoke-PnPSiteScript` uses to apply a script with only the caller's rights on the site (not yet measured on this
tenant: site/README.md, row S1). Running a script again updates what it made rather than adding a second copy, and
every column carries a fixed id, so the whole provisioning is safe to repeat. Starter rows are
added only where no row with the same Title exists, and nothing is ever deleted.

The flow file has the shape `build/prepare.py` writes for the FleetAgent build: `{name, definition, connectors,
connectionRefsTemplate}`, what the FlowAgent MCP tool `create_flow` takes.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import uuid
from xml.sax.saxutils import escape, quoteattr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
OUT = os.path.join(SITE, "out")
SPEC = os.path.join(SITE, "lists.json")
LISTS_MD = os.path.join(SITE, "LISTS.md")

SCRIPT_SCHEMA = "https://developer.microsoft.com/json-schemas/sp/site-design-script-actions.schema.json"
EXECUTE = "_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.ExecuteTemplateScript()"
SP_API = "/providers/Microsoft.PowerApps/apis/shared_sharepointonline"
#: Column ids are uuid5 of this namespace and `<list>/<column>`: fixed, so a script run twice finds its own columns.
ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/agentchieflou/Koa/site")
#: A synchronous site script run takes at most 30 actions, subactions included (site-design-overview).
MAX_ACTIONS = 30
TYPES = ("Text", "Note", "Choice", "Number", "Boolean", "DateTime", "URL", "User", "Lookup")
#: What Copilot in SharePoint can create when it builds a list (copilot-in-sharepoint-create-views).
COPILOT_TYPES = {"Text", "Note", "Choice", "Number", "Boolean", "DateTime", "URL"}
#: Every list and library already has these; views and formatters may name them.
BUILT_IN = {"Title", "LinkTitle", "ID", "Created", "Modified", "Author", "Editor", "DocIcon", "LinkFilename", "FileLeafRef"}
TEMPLATES = {100: "list", 101: "document library"}
TYPE_WORDS = {"Text": "single line of text", "Note": "multiple lines of plain text", "Choice": "choice",
              "Number": "number", "Boolean": "yes/no", "DateTime": "date", "URL": "hyperlink", "User": "person",
              "Lookup": "lookup"}


class Refused(Exception):
    pass


# ------------------------------------------------------------------------------------ the spec


def load_spec(path: str = SPEC) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)["lists"]


def formatter(rel: str) -> dict:
    with open(os.path.join(SITE, rel), encoding="utf-8") as f:
        return json.load(f)


def column_id(list_name: str, column: str) -> str:
    return "{" + str(uuid.uuid5(ID_NAMESPACE, f"{list_name}/{column}")) + "}"


def display(col: dict) -> str:
    return col.get("display", col["name"])


def check(lists: list[dict]) -> list[str]:
    """Every problem with the spec, in words; empty when it is sound."""
    problems = []
    names = [entry["name"] for entry in lists]
    seen: set[str] = set()
    for entry in lists:
        name = entry["name"]
        where = f"lists.json {name}"
        if entry.get("template") not in TEMPLATES:
            problems.append(f"{where}: template must be one of {sorted(TEMPLATES)}")
        cols = {c["name"]: c for c in entry["columns"]}
        if len(cols) != len(entry["columns"]):
            problems.append(f"{where}: a column name is used twice")
        displays = [display(c) for c in entry["columns"]]
        if len(set(displays)) != len(displays):
            problems.append(f"{where}: a display name is used twice")
        for col in entry["columns"]:
            if col["type"] not in TYPES:
                problems.append(f"{where}.{col['name']}: unknown type {col['type']}")
            if not col["name"].isidentifier() or not col["name"].isascii():
                problems.append(f"{where}.{col['name']}: an internal name is ASCII letters and digits only")
            if col["type"] == "Choice":
                if not col.get("choices"):
                    problems.append(f"{where}.{col['name']}: a choice column needs choices")
                if "default" in col and col["default"] not in col["choices"]:
                    problems.append(f"{where}.{col['name']}: the default is not one of the choices")
            if col["type"] == "Lookup":
                target = col.get("lookup")
                if target not in seen:
                    problems.append(f"{where}.{col['name']}: looks up {target}, which must come earlier in lists.json")
        known = set(cols) | BUILT_IN
        for field, rel in entry.get("formatters", {}).items():
            if field not in cols:
                problems.append(f"{where}: a formatter names {field}, which is not a column")
            if not os.path.exists(os.path.join(SITE, rel)):
                problems.append(f"{where}: {rel} does not exist")
        view_names = [v["name"] for v in entry["views"]]
        if len(set(view_names)) != len(view_names):
            problems.append(f"{where}: a view name is used twice")
        for view in entry["views"]:
            for field in view["fields"]:
                if field not in known:
                    problems.append(f"{where} view {view['name']}: {field} is not a column")
            if view.get("formatter") and not os.path.exists(os.path.join(SITE, view["formatter"])):
                problems.append(f"{where} view {view['name']}: {view['formatter']} does not exist")
        for n, row in enumerate(entry.get("seed", []), 1):
            if not row.get("Title"):
                problems.append(f"{where} seed {n}: every starter row has a Title")
            for key, value in row.items():
                if key == "Title":
                    continue
                col = cols.get(key)
                if col is None:
                    problems.append(f"{where} seed {n}: {key} is not a column")
                elif col["type"] in ("User", "Lookup"):
                    problems.append(f"{where} seed {n}: {key} is a {col['type']} column, which starter rows leave empty")
                elif col["type"] == "Choice" and value not in col["choices"]:
                    problems.append(f"{where} seed {n}: {value!r} is not a choice of {key}")
                elif col["type"] == "URL" and not (isinstance(value, dict) and value.get("url", "").startswith("https://")):
                    problems.append(f"{where} seed {n}: {key} is {{\"url\": \"https://...\", \"desc\": ...}}")
        titles = [row.get("Title") for row in entry.get("seed", [])]
        if len(set(titles)) != len(titles):
            problems.append(f"{where}: two starter rows share a Title, so the second would never be added")
        if action_count(entry) > MAX_ACTIONS:
            problems.append(f"{where}: {action_count(entry)} actions; a site script run takes at most {MAX_ACTIONS}")
        seen.add(name)
    if len(set(names)) != len(names):
        problems.append("lists.json: a list name is used twice")
    return problems


def require_sound(lists: list[dict]) -> None:
    problems = check(lists)
    if problems:
        raise Refused("site/lists.json is not sound:\n  " + "\n  ".join(problems))


# ------------------------------------------------------------------------------------ site scripts


def field_xml(list_name: str, col: dict) -> str:
    attrs = {"ID": column_id(list_name, col["name"]), "Name": col["name"], "StaticName": col["name"],
             "DisplayName": display(col), "Required": "TRUE" if col.get("required") else "FALSE"}
    if col.get("description"):
        attrs["Description"] = col["description"]
    kind = col["type"]
    inner = ""
    if kind == "Text":
        attrs.update(Type="Text", MaxLength="255")
    elif kind == "Note":
        attrs.update(Type="Note", NumLines="6", RichText="FALSE", AppendOnly="FALSE")
    elif kind == "Choice":
        attrs.update(Type="Choice", Format="Dropdown", FillInChoice="FALSE")
        if "default" in col:
            inner += f"<Default>{escape(col['default'])}</Default>"
        inner += "<CHOICES>" + "".join(f"<CHOICE>{escape(c)}</CHOICE>" for c in col["choices"]) + "</CHOICES>"
    elif kind == "Number":
        attrs.update(Type="Number", Decimals="0")
    elif kind == "Boolean":
        attrs.update(Type="Boolean")
        inner = "<Default>0</Default>"
    elif kind == "DateTime":
        attrs.update(Type="DateTime", Format="DateOnly")
    elif kind == "URL":
        attrs.update(Type="URL", Format="Hyperlink")
    elif kind == "User":
        attrs.update(Type="User", List="UserInfo", ShowField="ImnName", UserSelectionMode="PeopleOnly", UserSelectionScope="0")
    elif kind == "Lookup":
        attrs.update(Type="Lookup", ShowField="Title")
    order = ["Type", "ID", "Name", "StaticName", "DisplayName", "Required"]
    keys = order + [k for k in attrs if k not in order]
    head = "<Field " + " ".join(f"{k}={quoteattr(attrs[k])}" for k in keys)
    return head + (f">{inner}</Field>" if inner else " />")


def site_script(entry: dict) -> dict:
    name = entry["name"]
    sub: list[dict] = [{"verb": "setDescription", "description": entry["description"]}]
    for col in entry["columns"]:
        if col["type"] == "Lookup":
            sub.append({"verb": "addSPLookupFieldXml", "schemaXml": field_xml(name, col), "targetListName": col["lookup"]})
        else:
            sub.append({"verb": "addSPFieldXml", "schemaXml": field_xml(name, col)})
    cols = {c["name"]: c for c in entry["columns"]}
    for field, rel in entry.get("formatters", {}).items():
        sub.append({"verb": "setSPFieldCustomFormatter", "fieldDisplayName": display(cols[field]), "formatterJSON": formatter(rel)})
    for view in entry["views"]:
        action = {"verb": "addSPView", "name": view["name"], "viewFields": view["fields"], "query": view["query"],
                  "rowLimit": view["rowLimit"], "isPaged": True}
        if view.get("replace"):
            action["replaceViewFields"] = True
        if view.get("type2"):
            action["viewType2"] = view["type2"]
        if view.get("formatter"):
            action["formatterJSON"] = formatter(view["formatter"])
        sub.append(action)
    return {"$schema": SCRIPT_SCHEMA, "actions": [
        {"verb": "createSPList", "listName": name, "templateType": entry["template"], "subactions": sub}]}


def action_count(entry: dict) -> int:
    return 1 + 1 + len(entry["columns"]) + len(entry.get("formatters", {})) + len(entry["views"])


def scripts(lists: list[dict]) -> list[tuple[str, dict]]:
    require_sound(lists)
    return [(entry["name"], site_script(entry)) for entry in lists]


# ------------------------------------------------------------------------------------ starter rows


def entity_type(name: str) -> str:
    """The REST type of an item in a list made by createSPList: the list's URL name, then ListItem."""
    return f"SP.Data.{name[0].upper()}{name[1:]}ListItem"


def row_body(entry: dict, row: dict) -> dict:
    cols = {c["name"]: c for c in entry["columns"]}
    body: dict = {"__metadata": {"type": entity_type(entry["name"])}}
    for key, value in row.items():
        if key != "Title" and cols[key]["type"] == "URL":
            body[key] = {"__metadata": {"type": "SP.FieldUrlValue"}, "Url": value["url"], "Description": value.get("desc", value["url"])}
        else:
            body[key] = value
    return body


def seed(lists: list[dict]) -> list[dict]:
    require_sound(lists)
    return [{"list": entry["name"], "rows": [{"title": row["Title"], "body": row_body(entry, row)} for row in entry["seed"]]}
            for entry in lists if entry.get("seed")]


# ------------------------------------------------------------------------------------ the flow


def _compact(data) -> str:
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def _sp(method: str, uri: str, site: str, body: str | None = None, run_after: dict | None = None) -> dict:
    headers = {"Accept": "application/json;odata=nometadata"}
    params = {"dataset": site, "parameters/method": method, "parameters/uri": uri, "parameters/headers": headers}
    if body is not None:
        headers["Content-Type"] = "application/json;odata=verbose"
        params["parameters/body"] = body
    return {"type": "OpenApiConnection", "runAfter": run_after or {},
            "inputs": {"host": {"connectionName": "shared_sharepointonline", "operationId": "HttpRequest", "apiId": SP_API},
                       "parameters": params}}


def check_site(site: str) -> str:
    site = (site or "").rstrip("/")
    if not site.startswith("https://") or ".sharepoint.com/" not in site + "/":
        raise Refused("--site is the site's address, https://<tenant>.sharepoint.com/sites/<name>")
    return site


def provisioning_flow(site: str, lists: list[dict]) -> dict:
    """A one-shot manual flow: every site script in order, then every missing starter row. Safe to run again."""
    site = check_site(site)
    each_list = "@{items('For_each_seed_list')?['list']}"
    row_actions = {
        "Row_is_missing": {
            "type": "If", "runAfter": {},
            "expression": {"and": [{"not": {"contains": ["@body('Select_titles')", "@items('For_each_row')?['title']"]}}]},
            "actions": {"Add_row": _sp("POST", f"_api/web/lists/getbytitle('{each_list}')/items", site,
                                       body="@{items('For_each_row')?['body']}")},
            "else": {"actions": {}},
        },
    }
    seed_actions = {
        "Get_titles": _sp("GET", f"_api/web/lists/getbytitle('{each_list}')/items?$select=Title&$top=5000", site),
        "Select_titles": {"type": "Select", "runAfter": {"Get_titles": ["Succeeded"]},
                          "inputs": {"from": "@body('Get_titles')?['value']", "select": "@item()?['Title']"}},
        "For_each_row": {"type": "Foreach", "foreach": "@items('For_each_seed_list')?['rows']",
                         "runAfter": {"Select_titles": ["Succeeded"]},
                         "runtimeConfiguration": {"concurrency": {"repetitions": 1}}, "actions": row_actions},
    }
    script_items = [{"list": name, "body": _compact({"script": _compact(script)})} for name, script in scripts(lists)]
    seed_items = [{"list": s["list"], "rows": [{"title": r["title"], "body": _compact(r["body"])} for r in s["rows"]]}
                  for s in seed(lists)]
    definition = {
        "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {"$authentication": {"defaultValue": {}, "type": "SecureObject"},
                       "$connections": {"defaultValue": {}, "type": "Object"}},
        "triggers": {"manual": {"type": "Request", "kind": "Button",
                                "inputs": {"schema": {"type": "object", "properties": {}, "required": []}}}},
        "actions": {
            "Scripts": {"type": "Compose", "runAfter": {}, "inputs": script_items},
            "For_each_script": {"type": "Foreach", "foreach": "@outputs('Scripts')", "runAfter": {"Scripts": ["Succeeded"]},
                                "runtimeConfiguration": {"concurrency": {"repetitions": 1}},
                                "actions": {"Apply_script": _sp("POST", EXECUTE, site, body="@{items('For_each_script')?['body']}")}},
            "Seed": {"type": "Compose", "runAfter": {"For_each_script": ["Succeeded"]}, "inputs": seed_items},
            "For_each_seed_list": {"type": "Foreach", "foreach": "@outputs('Seed')", "runAfter": {"Seed": ["Succeeded"]},
                                   "runtimeConfiguration": {"concurrency": {"repetitions": 1}}, "actions": seed_actions},
        },
        "description": "Data Czars site: applies one site script per list, then adds the missing starter rows; safe to run again.",
    }
    modes = {"shared_sharepointonline": "Embedded"}
    return {"name": "CzarsProvisionSite", "definition": definition, "connectors": modes,
            "connectionRefsTemplate": {key: {"connectionName": "<pick_or_create_connection>", "source": mode,
                                             "id": f"/providers/Microsoft.PowerApps/apis/{key}", "tier": "NotSpecified"}
                                       for key, mode in modes.items()}}


# ------------------------------------------------------------------------------------ the console fallback


CONSOLE = """// Data Czars site: the lists, their views and the starter rows (site/README.md, step 2, the console way).
// Paste into the browser's developer console on {site}, signed in as a site owner, and press Enter.
// Safe to run again: scripts update what they made, and a row is added only when its Title is missing.
(async () => {{
  const site = {site_js};
  const scripts = {scripts_js};
  const seed = {seed_js};
  const json = 'application/json;odata=nometadata';
  const ctx = await fetch(site + '/_api/contextinfo', {{ method: 'POST', headers: {{ Accept: json }} }});
  const digest = (await ctx.json()).FormDigestValue;
  const post = (path, body) => fetch(site + '/' + path, {{ method: 'POST', body,
    headers: {{ Accept: json, 'Content-Type': 'application/json;odata=verbose', 'X-RequestDigest': digest }} }});
  for (const s of scripts) {{
    const r = await post({execute_js}, s.body);
    console.log('script', s.list, r.status, r.ok ? await r.json() : await r.text());
    if (!r.ok) return;
  }}
  for (const l of seed) {{
    const have = await fetch(site + `/_api/web/lists/getbytitle('${{l.list}}')/items?$select=Title&$top=5000`, {{ headers: {{ Accept: json }} }});
    const titles = new Set((await have.json()).value.map((x) => x.Title));
    for (const row of l.rows) {{
      if (titles.has(row.title)) continue;
      const r = await post(`_api/web/lists/getbytitle('${{l.list}}')/items`, row.body);
      console.log('row', l.list, row.title, r.status);
    }}
  }}
  console.log('done');
}})();
"""


def console_script(site: str, lists: list[dict]) -> str:
    site = check_site(site)
    script_items = [{"list": name, "body": _compact({"script": _compact(script)})} for name, script in scripts(lists)]
    seed_items = [{"list": s["list"], "rows": [{"title": r["title"], "body": _compact(r["body"])} for r in s["rows"]]}
                  for s in seed(lists)]
    return CONSOLE.format(site=site, site_js=json.dumps(site), execute_js=json.dumps(EXECUTE),
                          scripts_js=json.dumps(script_items, ensure_ascii=False),
                          seed_js=json.dumps(seed_items, ensure_ascii=False))


# ------------------------------------------------------------------------------------ LISTS.md


def _choices(col: dict) -> str:
    text = ", ".join(col["choices"])
    if "default" in col:
        text += f" (default {col['default']})"
    return text


def copilot_prompt(entry: dict) -> str:
    kind = TEMPLATES[entry["template"]]
    lines = [f"Create a {kind} called \"{entry['name']}\" with the description \"{entry['description']}\"",
             "Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:"]
    for col in entry["columns"]:
        if col["type"] not in COPILOT_TYPES:
            continue
        words = TYPE_WORDS[col["type"]]
        if col["type"] == "Choice":
            words += f" with the choices {_choices(col)}"
        if col.get("required"):
            words += ", required"
        lines.append(f"- {col['name']}: {words}.")
    lines.append("Propose the structure first and wait for my go-ahead before you create it.")
    return "\n".join(lines)


def docs(lists: list[dict]) -> str:
    require_sound(lists)
    out = ["# The site's lists", "",
           "Generated from `site/lists.json` by `python site/provision.py docs`; `tests/test_site.py` fails when this page and",
           "the spec disagree, so edit the spec and regenerate rather than editing here.", "",
           "Every list is made by one site script (`python site/provision.py scripts`), applied in this order because a",
           "lookup column needs its target list to exist first. The **Copilot fallback** under each list is for a tenant",
           "where neither the provisioning flow nor the console can run: Copilot in SharePoint creates the columns it",
           "supports, and the rest is done by hand as the list says.", ""]
    for n, entry in enumerate(lists, 1):
        name = entry["name"]
        out += [f"## {n}. {name}", "", f"{entry['description']} A {TEMPLATES[entry['template']]}, "
                f"{action_count(entry)} script actions, {len(entry.get('seed', []))} starter rows.", "",
                "| Column | Shown as | Type | Notes |", "| --- | --- | --- | --- |"]
        for col in entry["columns"]:
            notes = []
            if col["type"] == "Choice":
                notes.append(_choices(col))
            if col["type"] == "Lookup":
                notes.append(f"looks up {col['lookup']}")
            if col.get("required"):
                notes.append("required")
            if col.get("description"):
                notes.append(col["description"])
            out.append(f"| `{col['name']}` | {display(col)} | {TYPE_WORDS[col['type']]} | {'; '.join(notes)} |")
        out += ["", "| View | Shows | Layout |", "| --- | --- | --- |"]
        for view in entry["views"]:
            layout = "gallery" if view.get("type2") == "TILES" else "list"
            if view.get("formatter"):
                layout += f", `{view['formatter']}`"
            out.append(f"| {view['name']} | {', '.join(f'`{f}`' for f in view['fields'])} | {layout} |")
        if entry.get("formatters"):
            out += ["", "Column formatting: " + ", ".join(f"`{f}` with `{rel}`" for f, rel in entry["formatters"].items()) + "."]
        by_hand = [c for c in entry["columns"] if c["type"] not in COPILOT_TYPES]
        out += ["", "**Copilot fallback.** In Copilot in SharePoint on the site, paste:", "", "```text", copilot_prompt(entry), "```", ""]
        steps = []
        if by_hand:
            steps.append("add by hand " + ", ".join(f"`{c['name']}` ({TYPE_WORDS[c['type']]}"
                                                     + (f" to {c['lookup']}" if c["type"] == "Lookup" else "") + ")" for c in by_hand))
        steps.append("rename each column to its *Shown as* name (the internal name stays)")
        if entry.get("formatters"):
            steps.append("paste each column formatter in **Format this column** > **Advanced mode**")
        if any(v.get("formatter") or v.get("type2") for v in entry["views"]):
            steps.append("create the views above and paste each view's formatter in **Format current view** > **Advanced mode**")
        out += ["Then " + "; ".join(steps) + ".", ""]
    return "\n".join(out).rstrip("\n") + "\n"


# ------------------------------------------------------------------------------------ files


def _write(path: str, text: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


def _show(path: str) -> str:
    try:
        return os.path.relpath(path)
    except ValueError:
        return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="provision.py", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("scripts")
    for name in ("flow", "console"):
        sub.add_parser(name).add_argument("--site", required=True, help="https://<tenant>.sharepoint.com/sites/<name>")
    sub.add_parser("docs")
    args = parser.parse_args(argv)
    lists = load_spec()
    try:
        if args.cmd == "check":
            require_sound(lists)
            print(f"ok: {len(lists)} lists, {sum(len(e['columns']) for e in lists)} columns, "
                  f"{sum(len(e['views']) for e in lists)} views, {sum(len(e.get('seed', [])) for e in lists)} starter rows")
        elif args.cmd == "scripts":
            for n, (name, script) in enumerate(scripts(lists), 1):
                path = _write(os.path.join(OUT, "scripts", f"{n:02d}-{name}.json"), json.dumps(script, indent=2, ensure_ascii=False) + "\n")
                print(_show(path))
        elif args.cmd == "flow":
            package = provisioning_flow(args.site, lists)
            print(_show(_write(os.path.join(OUT, f"{package['name']}.json"), json.dumps(package, indent=2, ensure_ascii=False) + "\n")))
        elif args.cmd == "console":
            print(_show(_write(os.path.join(OUT, "provision.console.js"), console_script(args.site, lists))))
        elif args.cmd == "docs":
            print(_show(_write(LISTS_MD, docs(lists))))
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
