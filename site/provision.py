#!/usr/bin/env python3
"""Turn the site's spec and the scanned context into what SharePoint and Copilot take (site/README.md). Stdlib only.

    python site/provision.py context                 merge site/local/context/*.json into site/local/context.json
    python site/provision.py check                   the spec (and the context, when there is one) is sound
    python site/provision.py scripts                 site/out/scripts/NN-<List>.json: one site script per list
    python site/provision.py flow                    site/out/CzarsProvisionSite.json: a one-shot flow for FlowAgent
    python site/provision.py console                 site/out/provision.console.js: the same, pasted in the browser
    python site/provision.py pages                   site/out/pages/*.md and site/out/agents/*: prompts with the facts in
    python site/provision.py flows --results-folder-id <id>
                                                     site/out/CzarsIntakeOut.json, CzarsIntakeBack.json (Intake <-> Jira)
                                                     and CzarsTagReports.json (usage reports tagged by their folder)
    python site/provision.py docs                    rewrite site/LISTS.md from the spec

Two inputs, kept apart on purpose because Koa is public:

- `site/lists.json` (tracked) is the structure: every list, column, view, formatter and the starter rows that hold no
  internal fact. `site/formatting/*.json` are the formatters it names.
- `site/local/context.json` (git-ignored) is what the scans found in data-czars, usage_tool and the fleet, and what
  Microsoft 365 Copilot knows about the team (`.github/prompts/czars-*.prompt.md`, `site/prompts/`). It becomes list
  rows, choice values (`choicesFrom`), and the `{{...}}` facts in the page sheets and agent files. Its shape is
  `site/context.example.json`.

Each list becomes one site script (`createSPList` with its columns, formatters and views as subactions), applied in
order by SharePoint's `ExecuteTemplateScript` endpoint, the one PnP's `Invoke-PnPSiteScript` uses to apply a script
with only the caller's rights on the site (not yet measured on this tenant: site/README.md, row S1). Running a script
again updates what it made, every column carries a fixed id, and a row is added only where no row with the same
Title exists, so the whole provisioning is safe to repeat. Nothing is ever deleted.

The flow file has the shape `build/prepare.py` writes for the FleetAgent build: `{name, definition, connectors,
connectionRefsTemplate}`, what the FlowAgent MCP tool `create_flow` takes.
"""
from __future__ import annotations
import argparse
import copy
import glob
import json
import os
import re
import sys
import uuid
from xml.sax.saxutils import escape, quoteattr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
OUT = os.path.join(SITE, "out")
LOCAL = os.path.join(SITE, "local")
SPEC = os.path.join(SITE, "lists.json")
CONTEXT = os.path.join(LOCAL, "context.json")
CONTEXT_PARTS = os.path.join(LOCAL, "context")
LISTS_MD = os.path.join(SITE, "LISTS.md")

SCRIPT_SCHEMA = "https://developer.microsoft.com/json-schemas/sp/site-design-script-actions.schema.json"
EXECUTE = "_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.ExecuteTemplateScript()"
SP_API = "/providers/Microsoft.PowerApps/apis/shared_sharepointonline"
OD_API = "/providers/Microsoft.PowerApps/apis/shared_onedriveforbusiness"
#: The operator's OneDrive folder the intake flows and site/intake/intake.py share: intake/ out, results/ back.
INTAKE_FOLDER = "/DataCzars"
#: Column ids are uuid5 of this namespace and `<list>/<column>`: fixed, so a script run twice finds its own columns.
ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/agentchieflou/Koa/site")
#: A synchronous site script run takes at most 30 actions, subactions included (site-design-overview).
MAX_ACTIONS = 30
TYPES = ("Text", "Note", "Choice", "Number", "Boolean", "DateTime", "URL", "User", "Lookup")
#: What Copilot in SharePoint can create when it builds a list (copilot-in-sharepoint-create-views).
COPILOT_TYPES = {"Text", "Note", "Choice", "Number", "Boolean", "DateTime", "URL"}
#: Every list and library already has these; views and formatters may name them.
BUILT_IN = {"Title", "LinkTitle", "ID", "Created", "Modified", "Author", "Editor", "DocIcon", "LinkFilename",
            "FileLeafRef", "FileRef"}
TEMPLATES = {100: "list", 101: "document library"}
TYPE_WORDS = {"Text": "single line of text", "Note": "multiple lines of plain text", "Choice": "choice",
              "Number": "number", "Boolean": "yes/no", "DateTime": "date", "URL": "hyperlink", "User": "person",
              "Lookup": "lookup"}
PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_.\[\]]+)\s*\}\}")
#: The context's sections and the scan or prompt that owns each (site/README.md, step 0).
SECTIONS = {"site": dict, "team": dict, "jira": dict, "products": list, "usageTool": dict, "fleet": dict,
            "links": list, "contacts": list, "releases": list, "faq": list, "gaps": list}
#: The key that makes two entries of a context list the same entry when the parts are merged.
IDENTITY = {"products": ("name",), "links": ("url",), "contacts": ("email",), "releases": ("product", "version"),
            "faq": ("question",), "gaps": ()}


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


def column(lists: list[dict], list_name: str, col_name: str) -> dict:
    entry = next(e for e in lists if e["name"] == list_name)
    return next(c for c in entry["columns"] if c["name"] == col_name)


# ------------------------------------------------------------------------------------ the context


def lookup(ctx: dict, path: str):
    """`team.mission`, `products[].category` (every product's category) or `usageTool.reportTypes[].name`."""
    values = [ctx]
    for part in path.split("."):
        many = part.endswith("[]")
        key = part[:-2] if many else part
        nxt = []
        for value in values:
            if not isinstance(value, dict) or key not in value:
                continue
            got = value[key]
            if many:
                nxt.extend(got if isinstance(got, list) else [])
            else:
                nxt.append(got)
        values = nxt
    if "[]" in path:
        return values
    return values[0] if values else None


def _text(value) -> str:
    """A fact as words: a list of sentences runs on as prose, any other list is joined with commas."""
    if isinstance(value, list):
        items = [_text(v) for v in value if _text(v).strip()]
        sentences = items and all(i.rstrip().endswith((".", "!", "?")) for i in items)
        return (" " if sentences else ", ").join(items)
    if isinstance(value, bool):
        return "yes" if value else "no"
    return "" if value is None else str(value)


def render(text: str, ctx: dict, where: str) -> str:
    """Every `{{path}}` replaced by the context's value; a missing or empty fact is refused by name."""
    missing = []

    def sub(m):
        value = lookup(ctx, m.group(1))
        out = _text(value)
        if not out.strip():
            missing.append(m.group(1))
        return out
    result = PLACEHOLDER.sub(sub, text)
    if missing:
        raise Refused(f"{where} needs {', '.join(sorted(set(missing)))} in site/local/context.json")
    return result


def placeholders(text: str) -> set[str]:
    return set(PLACEHOLDER.findall(text))


def _empty(value) -> bool:
    return value in ("", None, [], {})


def _merge_into(base: dict, part: dict, name: str, notes: list[str]) -> None:
    for key, value in part.items():
        if key not in base or _empty(base[key]):
            base[key] = copy.deepcopy(value)
        elif isinstance(base[key], dict) and isinstance(value, dict):
            _merge_into(base[key], value, f"{name}.{key}", notes)
        elif not _empty(value) and base[key] != value:
            notes.append(f"{name}.{key}: kept {base[key]!r}, ignored {value!r}")


def merge_context(parts: list[tuple[str, dict]]) -> tuple[dict, list[str]]:
    """The parts in file-name order: dictionaries merge (the first non-empty value wins, a conflict is noted), lists
    join with one entry per identity (a product by name, a link by url, a contact by email)."""
    ctx: dict = {}
    notes: list[str] = []
    for source, part in parts:
        for key, value in part.items():
            if key not in SECTIONS:
                notes.append(f"{source}: {key} is not a context section; ignored")
                continue
            if SECTIONS[key] is list:
                have = ctx.setdefault(key, [])
                ident = IDENTITY[key]
                seen = {tuple(str(x.get(k, "")).lower() for k in ident) for x in have if ident}
                for item in value:
                    mark = tuple(str(item.get(k, "")).lower() for k in ident) if ident else None
                    if ident and mark in seen:
                        notes.append(f"{source}: {key} {'/'.join(mark)} is already there; kept the first")
                        continue
                    if not ident and item in have:
                        continue
                    have.append(copy.deepcopy(item))
                    if ident:
                        seen.add(mark)
            else:
                base = ctx.setdefault(key, {})
                _merge_into(base, value, key, notes)
    return ctx, notes


def _choices_of(lists: list[dict], list_name: str, col_name: str) -> list[str]:
    return column(lists, list_name, col_name)["choices"]


def check_context(ctx: dict, lists: list[dict]) -> list[str]:
    """Every problem with the merged context, in words; empty when it is sound."""
    problems = []
    for key, value in ctx.items():
        if key not in SECTIONS:
            problems.append(f"{key}: not a context section")
        elif not isinstance(value, SECTIONS[key]):
            problems.append(f"{key}: is a {SECTIONS[key].__name__}")
    if problems:
        return problems

    def url(value, where):
        if value and not str(value).startswith("https://"):
            problems.append(f"{where}: {value!r} is not an https address")

    def one_of(value, allowed, where):
        if value not in allowed:
            problems.append(f"{where}: {value!r} is not one of {', '.join(allowed)}")

    def strings(item, where):
        for k, v in item.items():
            if isinstance(v, str) and len(v) > 600:
                problems.append(f"{where}.{k}: longer than 600 characters")

    url(ctx.get("site", {}).get("url"), "site.url")
    if ctx.get("site", {}).get("url") and ".sharepoint.com/" not in ctx["site"]["url"] + "/":
        problems.append("site.url: is the site's address, https://<tenant>.sharepoint.com/sites/<name>")
    jira = ctx.get("jira", {})
    url(jira.get("url"), "jira.url")
    url(jira.get("boardUrl"), "jira.boardUrl")
    if jira.get("flavour"):
        one_of(jira["flavour"], ["Data Center", "Cloud"], "jira.flavour")
    days = ctx.get("team", {}).get("triageDays", "")
    if days and not str(days).isdigit():
        problems.append(f"team.triageDays: {days!r} is a whole number of business days")
    for n, p in enumerate(ctx.get("products", []), 1):
        where = f"products[{n}]"
        if not p.get("name"):
            problems.append(f"{where}: has no name")
        if p.get("supportLevel"):
            one_of(p["supportLevel"], _choices_of(lists, "Products", "SupportLevel"), f"{where}.supportLevel")
        if p.get("status"):
            one_of(p["status"], _choices_of(lists, "Products", "Status"), f"{where}.status")
        for k in ("docs", "repo"):
            if p.get(k):
                url(p[k].get("url"), f"{where}.{k}.url")
        strings(p, where)
    for n, link in enumerate(ctx.get("links", []), 1):
        where = f"links[{n}]"
        if not link.get("title") or not link.get("url"):
            problems.append(f"{where}: needs a title and a url")
        url(link.get("url"), f"{where}.url")
        one_of(link.get("category", "Other"), _choices_of(lists, "Links", "Category"), f"{where}.category")
        one_of(link.get("shownTo", "Everyone"), _choices_of(lists, "Links", "ShownTo"), f"{where}.shownTo")
    for n, c in enumerate(ctx.get("contacts", []), 1):
        where = f"contacts[{n}]"
        if not c.get("name") or "@" not in c.get("email", ""):
            problems.append(f"{where}: needs a name and an email address")
        one_of(c.get("preferredMethod", "Teams chat"), _choices_of(lists, "Contacts", "PreferredMethod"), f"{where}.preferredMethod")
        one_of(c.get("shownTo", "Everyone"), _choices_of(lists, "Contacts", "ShownTo"), f"{where}.shownTo")
    names = [p.get("name") for p in ctx.get("products", [])]
    for n, r in enumerate(ctx.get("releases", []), 1):
        where = f"releases[{n}]"
        if r.get("product") not in names:
            problems.append(f"{where}: product {r.get('product')!r} is not one of the products")
        if not r.get("version") or not r.get("headline"):
            problems.append(f"{where}: needs a version and a headline")
        one_of(r.get("kind", "Notes"), _choices_of(lists, "Releases", "Kind"), f"{where}.kind")
        if r.get("date") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["date"]):
            problems.append(f"{where}.date: {r['date']!r} is YYYY-MM-DD")
    topics = _choices_of(lists, "FAQ", "Topic") + names
    for n, q in enumerate(ctx.get("faq", []), 1):
        where = f"faq[{n}]"
        if not q.get("question") or not q.get("answer"):
            problems.append(f"{where}: needs a question and an answer")
        one_of(q.get("topic", "Other"), topics, f"{where}.topic")
    for n, rt in enumerate(ctx.get("usageTool", {}).get("reportTypes", []), 1):
        where = f"usageTool.reportTypes[{n}]"
        if not rt.get("name"):
            problems.append(f"{where}: has no name")
        if rt.get("period"):
            one_of(rt["period"], _choices_of(lists, "UsageReports", "PeriodType"), f"{where}.period")
    return problems


def load_context(path: str | None = None) -> dict:
    path = path or CONTEXT
    if not os.path.exists(path):
        raise Refused(f"{_show(path)} does not exist yet: run the scans (site/README.md, step 0), then "
                      "`python site/provision.py context`")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def gaps(ctx: dict) -> list[str]:
    """What the site still needs from someone: the scans' own gaps, then every fact the pages use that is empty."""
    out = list(ctx.get("gaps", []))
    wanted = set()
    for path in glob.glob(os.path.join(SITE, "pages", "*.md")) + glob.glob(os.path.join(SITE, "agents", "*")):
        with open(path, encoding="utf-8") as f:
            wanted |= placeholders(f.read())
    for fact in sorted(wanted):
        if not _text(lookup(ctx, fact)).strip():
            out.append(f"{fact}: used by the pages, still empty")
    return out


# ------------------------------------------------------------------------------------ the spec, resolved


def _seed_rows(ctx: dict) -> dict[str, list[dict]]:
    """List rows from the context: the products, releases, links and contacts the scans found."""
    rows: dict[str, list[dict]] = {}

    def link(value):
        return {"url": value["url"], "desc": value.get("desc") or value["url"]} if value and value.get("url") else None

    for n, p in enumerate(ctx.get("products", []), 1):
        row = {"Title": p["name"], "Summary": p.get("summary", ""), "Category": p.get("category") or "Other",
               "SupportLevel": p.get("supportLevel") or "Supported", "Status": p.get("status") or "Operational",
               "CurrentVersion": p.get("version", ""), "HowToStart": p.get("howToStart", ""),
               "JiraComponent": p.get("jiraComponent", ""), "Featured": bool(p.get("featured")), "SortOrder": n * 10}
        for key, col in (("docs", "DocsLink"), ("repo", "RepoLink")):
            if link(p.get(key)):
                row[col] = link(p[key])
        rows.setdefault("Products", []).append(row)
    for r in ctx.get("releases", []):
        row = {"Title": f"{r['product']} {r['version']}", "Headline": r["headline"], "Product": r["product"],
               "Kind": r.get("kind") or "Notes", "ReleaseNotes": r.get("notes", "")}
        if r.get("date"):
            row["ReleasedOn"] = r["date"]
        rows.setdefault("Releases", []).append(row)
    for n, item in enumerate(ctx.get("links", []), 1):
        rows.setdefault("Links", []).append({"Title": item["title"], "Url": {"url": item["url"], "desc": item["title"]},
                                             "Category": item.get("category") or "Other",
                                             "LinkDescription": item.get("description", ""),
                                             "ShownTo": item.get("shownTo") or "Everyone", "SortOrder": n * 10})
    for n, c in enumerate(ctx.get("contacts", []), 1):
        rows.setdefault("Contacts", []).append({"Title": c["name"], "Email": c["email"], "Role": c.get("role", ""),
                                                "Topics": c.get("topics", ""),
                                                "PreferredMethod": c.get("preferredMethod") or "Teams chat",
                                                "WorkingHours": c.get("workingHours", ""),
                                                "ShownTo": c.get("shownTo") or "Everyone", "SortOrder": n * 10})
    for n, q in enumerate(ctx.get("faq", []), 1):
        rows.setdefault("FAQ", []).append({"Title": q["question"], "Answer": q["answer"], "Topic": q.get("topic") or "Other",
                                           "ShownTo": q.get("shownTo") or "Everyone", "SortOrder": 100 + n * 10})
    for entry in rows.values():
        for row in entry:
            for key in [k for k, v in row.items() if v == ""]:
                del row[key]
    return rows


def resolve(lists: list[dict], ctx: dict | None) -> list[dict]:
    """The spec as it goes to the site: with a context, `choicesFrom` adds the scanned values to a choice column, the
    starter rows' `{{facts}}` are filled in, and the context's rows are added after them."""
    out = copy.deepcopy(lists)
    if ctx is None:
        return out
    rows = _seed_rows(ctx)
    for entry in out:
        for col in entry["columns"]:
            if col.get("choicesFrom"):
                found = [str(v) for v in lookup(ctx, col["choicesFrom"]) if str(v).strip()]
                col["choices"] = list(dict.fromkeys(found + col["choices"]))
        entry["seed"] = [{k: render(v, ctx, f"lists.json {entry['name']} seed") if isinstance(v, str) else v
                          for k, v in row.items()} for row in entry.get("seed", [])]
        entry["seed"] += rows.get(entry["name"], [])
    return out


def check(lists: list[dict], ctx: dict | None = None) -> list[str]:
    """Every problem with the spec (resolved against the context, when there is one), in words; empty when sound."""
    problems = []
    if ctx is not None:
        problems += [f"context {p}" for p in check_context(ctx, lists)]
        if problems:
            return problems
        lists = resolve(lists, ctx)
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
            if col.get("choicesFrom") and (col["type"] != "Choice" or col["choicesFrom"].split(".")[0].rstrip("[]") not in SECTIONS):
                problems.append(f"{where}.{col['name']}: choicesFrom names a context section, on a choice column")
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


def require_sound(lists: list[dict], ctx: dict | None = None) -> None:
    problems = check(lists, ctx)
    if problems:
        raise Refused("the site's spec is not sound:\n  " + "\n  ".join(problems))


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


def scripts(lists: list[dict], ctx: dict | None = None) -> list[tuple[str, dict]]:
    require_sound(lists, ctx)
    return [(entry["name"], site_script(entry)) for entry in resolve(lists, ctx)]


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


def seed(lists: list[dict], ctx: dict) -> list[dict]:
    require_sound(lists, ctx)
    return [{"list": entry["name"], "rows": [{"title": row["Title"], "body": row_body(entry, row)} for row in entry["seed"]]}
            for entry in resolve(lists, ctx) if entry.get("seed")]


# ------------------------------------------------------------------------------------ the flow


def _compact(data) -> str:
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def _sp(method: str, uri: str, site: str, body: str | None = None, run_after: dict | None = None,
        merge: bool = False) -> dict:
    headers = {"Accept": "application/json;odata=nometadata"}
    if merge:
        headers.update({"IF-MATCH": "*", "X-HTTP-Method": "MERGE"})
    params = {"dataset": site, "parameters/method": method, "parameters/uri": uri, "parameters/headers": headers}
    if body is not None:
        headers["Content-Type"] = "application/json;odata=verbose"
        params["parameters/body"] = body
    return {"type": "OpenApiConnection", "runAfter": run_after or {},
            "inputs": {"host": {"connectionName": "shared_sharepointonline", "operationId": "HttpRequest", "apiId": SP_API},
                       "parameters": params}}


def _package(name: str, definition: dict, modes: dict) -> dict:
    return {"name": name, "definition": definition, "connectors": modes,
            "connectionRefsTemplate": {key: {"connectionName": "<pick_or_create_connection>", "source": mode,
                                             "id": f"/providers/Microsoft.PowerApps/apis/{key}", "tier": "NotSpecified"}
                                       for key, mode in modes.items()}}


def _definition(triggers: dict, actions: dict, description: str) -> dict:
    return {"$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
            "contentVersion": "1.0.0.0",
            "parameters": {"$authentication": {"defaultValue": {}, "type": "SecureObject"},
                           "$connections": {"defaultValue": {}, "type": "Object"}},
            "triggers": triggers, "actions": actions, "description": description}


def check_site(site: str) -> str:
    site = (site or "").rstrip("/")
    if not site.startswith("https://") or ".sharepoint.com/" not in site + "/":
        raise Refused("the site's address is https://<tenant>.sharepoint.com/sites/<name> (site.url in the context, or --site)")
    return site


def _payloads(lists: list[dict], ctx: dict) -> tuple[list[dict], list[dict]]:
    script_items = [{"list": name, "body": _compact({"script": _compact(script)})} for name, script in scripts(lists, ctx)]
    seed_items = [{"list": s["list"], "rows": [{"title": r["title"], "body": _compact(r["body"])} for r in s["rows"]]}
                  for s in seed(lists, ctx)]
    return script_items, seed_items


def provisioning_flow(site: str, lists: list[dict], ctx: dict) -> dict:
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
    script_items, seed_items = _payloads(lists, ctx)
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
    return _package("CzarsProvisionSite", definition, {"shared_sharepointonline": "Embedded"})


# ------------------------------------------------------------------------------------ Intake <-> Jira


INTAKE_ROW = "_api/web/lists/getbytitle('Intake')/items(@{%s})"
INTAKE_FIELDS = {"kind": "intake", "id": "ID", "title": "Title", "type": "IntakeType/Value", "product": "Product/Value",
                 "details": "Details", "impact": "Impact/Value", "affectedTeam": "AffectedTeam", "neededBy": "NeededBy",
                 "requester": "Author/Email", "requesterName": "Author/DisplayName", "created": "Created", "link": "{Link}"}


def intake_out_flow(site: str, folder: str = INTAKE_FOLDER) -> dict:
    """A new Intake row becomes `<folder>/intake/intake-<id>.json` in the operator's OneDrive, for intake.py to file."""
    site = check_site(site)
    row = {k: (v if k == "kind" else f"@triggerOutputs()?['body/{v}']") for k, v in INTAKE_FIELDS.items()}
    waiting = _compact({"__metadata": {"type": "SP.Data.IntakeListItem"},
                        "SyncNote": "Waiting to be filed in Jira: the team's laptop files it after one approval."})
    triggers = {"When_an_intake_row_is_created": {
        "type": "OpenApiConnection", "recurrence": {"frequency": "Minute", "interval": 1},
        "splitOn": "@triggerOutputs()?['body/value']",
        "inputs": {"host": {"connectionName": "shared_sharepointonline", "operationId": "GetOnNewItems", "apiId": SP_API},
                   "parameters": {"dataset": site, "table": "Intake"}}}}
    actions = {
        "Intake_file": {"type": "Compose", "runAfter": {}, "inputs": row},
        "Create_intake_file": {"type": "OpenApiConnection", "runAfter": {"Intake_file": ["Succeeded"]},
                               "inputs": {"host": {"connectionName": "shared_onedriveforbusiness", "operationId": "CreateFile", "apiId": OD_API},
                                          "parameters": {"folderPath": f"{folder}/intake",
                                                         "name": "intake-@{triggerOutputs()?['body/ID']}.json",
                                                         "body": "@{outputs('Intake_file')}"}}},
        "Say_waiting": _sp("POST", INTAKE_ROW % "triggerOutputs()?['body/ID']", site, body=waiting,
                           run_after={"Create_intake_file": ["Succeeded"]}, merge=True),
    }
    return _package("CzarsIntakeOut", _definition(triggers, actions, "Data Czars: every new Intake row goes to the laptop to become a Jira ticket."),
                    {"shared_sharepointonline": "Embedded", "shared_onedriveforbusiness": "Embedded"})


def intake_back_flow(site: str, results_folder_id: str) -> dict:
    """A result file from intake.py (the Jira key, link, status and a sentence) is merged into its Intake row."""
    site = check_site(site)
    if not (results_folder_id or "").strip():
        raise Refused("--results-folder-id is the OneDrive id of <folder>/results (site/intake/README.md, step 2)")
    triggers = {"When_a_result_arrives": {
        "type": "OpenApiConnection", "recurrence": {"frequency": "Minute", "interval": 5},
        "splitOn": "@triggerOutputs()?['body/value']",
        "inputs": {"host": {"connectionName": "shared_onedriveforbusiness", "operationId": "OnNewFilesV2", "apiId": OD_API},
                   "parameters": {"folderId": results_folder_id, "includeSubfolders": False, "maxFileCount": 20}}}}
    actions = {
        "Get_file_content": {"type": "OpenApiConnection", "runAfter": {},
                             "inputs": {"host": {"connectionName": "shared_onedriveforbusiness", "operationId": "GetFileContent", "apiId": OD_API},
                                        "parameters": {"id": "@triggerOutputs()?['body/Id']", "inferContentType": False}}},
        "Result": {"type": "Compose", "runAfter": {"Get_file_content": ["Succeeded"]},
                   "inputs": "@json(base64ToString(body('Get_file_content')?['$content']))"},
        "Apply_to_row": _sp("POST", INTAKE_ROW % "outputs('Result')?['id']", site, body="@{string(outputs('Result')?['merge'])}",
                            run_after={"Result": ["Succeeded"]}, merge=True),
    }
    return _package("CzarsIntakeBack", _definition(triggers, actions, "Data Czars: the laptop's Jira key and status for an Intake row, written back to it."),
                    {"shared_sharepointonline": "Embedded", "shared_onedriveforbusiness": "Embedded"})


# ------------------------------------------------------------------------------------ usage reports


def tag_reports_flow(site: str) -> dict:
    """Every hour, a report with no type yet takes its type and period from where it landed:
    `UsageReports/<report type>/<yyyy-mm>/<file>`. The usage tool (or whoever copies its output) only picks the folder."""
    site = check_site(site)
    path = "split(items('For_each_report')?['{Path}'], '/')"
    body = ('{"__metadata":{"type":"SP.Data.UsageReportsItem"},'
            f'"ReportType":"@{{{path}[1]}}","PeriodStart":"@{{{path}[2]}}-01T00:00:00Z",'
            '"PeriodType":"Monthly","ReportStatus":"Published"}')
    triggers = {"Every_hour": {"type": "Recurrence", "recurrence": {"frequency": "Hour", "interval": 1}}}
    actions = {
        "Get_reports": {"type": "OpenApiConnection", "runAfter": {},
                        "inputs": {"host": {"connectionName": "shared_sharepointonline", "operationId": "GetFileItems", "apiId": SP_API},
                                   "parameters": {"dataset": site, "table": "UsageReports", "$orderby": "Created desc", "$top": 200}}},
        "For_each_report": {
            "type": "Foreach", "foreach": "@body('Get_reports')?['value']", "runAfter": {"Get_reports": ["Succeeded"]},
            "runtimeConfiguration": {"concurrency": {"repetitions": 1}},
            "actions": {"Is_untagged_in_a_dated_folder": {
                "type": "If", "runAfter": {},
                "expression": {"and": [
                    {"equals": ["@empty(items('For_each_report')?['ReportType']?['Value'])", True]},
                    {"equals": [f"@length({path})", 4]},
                    {"equals": [f"@isInt(replace({path}[2], '-', ''))", True]}]},
                "actions": {"Tag_report": _sp("POST", "_api/web/lists/getbytitle('UsageReports')/items(@{items('For_each_report')?['ID']})",
                                              site, body=body, merge=True)},
                "else": {"actions": {}}}}},
    }
    return _package("CzarsTagReports", _definition(triggers, actions, "Data Czars: usage reports take their type and period from their folder."),
                    {"shared_sharepointonline": "Embedded"})


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


def console_script(site: str, lists: list[dict], ctx: dict) -> str:
    site = check_site(site)
    script_items, seed_items = _payloads(lists, ctx)
    return CONSOLE.format(site=site, site_js=json.dumps(site), execute_js=json.dumps(EXECUTE),
                          scripts_js=json.dumps(script_items, ensure_ascii=False),
                          seed_js=json.dumps(seed_items, ensure_ascii=False))


# ------------------------------------------------------------------------------------ pages and agents


def rendered_files(ctx: dict) -> dict[str, str]:
    """Every page sheet and agent file with its facts filled in, by its path under site/out/."""
    out = {}
    for path in sorted(glob.glob(os.path.join(SITE, "pages", "*.md")) + glob.glob(os.path.join(SITE, "agents", "*"))):
        rel = os.path.relpath(path, SITE).replace(os.sep, "/")
        with open(path, encoding="utf-8") as f:
            out[rel] = render(f.read(), ctx, rel)
    return out


# ------------------------------------------------------------------------------------ LISTS.md


def _choices(col: dict) -> str:
    text = ", ".join(col["choices"])
    if col.get("choicesFrom"):
        text = f"from the scan (`{col['choicesFrom']}`), then " + text
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
            words += f" with the choices {', '.join(col['choices'])}"
            if "default" in col:
                words += f" (default {col['default']})"
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
           "lookup column needs its target list to exist first. A choice column marked *from the scan* also gets the values",
           "the scans found (`site/local/context.json`), ahead of the ones listed. The **Copilot fallback** under each list is",
           "for a tenant where neither the provisioning flow nor the console can run: Copilot in SharePoint creates the",
           "columns it supports, and the rest is done by hand as the list says.", ""]
    for n, entry in enumerate(lists, 1):
        name = entry["name"]
        out += [f"## {n}. {name}", "", f"{entry['description']} A {TEMPLATES[entry['template']]}, "
                f"{action_count(entry)} script actions, {len(entry.get('seed', []))} tracked starter rows.", "",
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
        if any(c.get("choicesFrom") for c in entry["columns"]):
            steps.append("add the scanned values to " + ", ".join(f"`{c['name']}`" for c in entry["columns"] if c.get("choicesFrom")))
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


def context_parts(folder: str = CONTEXT_PARTS) -> list[tuple[str, dict]]:
    parts = []
    for path in sorted(glob.glob(os.path.join(folder, "*.json"))):
        with open(path, encoding="utf-8") as f:
            try:
                parts.append((os.path.basename(path), json.load(f)))
            except json.JSONDecodeError as e:
                raise Refused(f"{_show(path)} is not valid JSON: {e}")
    if not parts:
        raise Refused(f"no scan results in {_show(folder)}: run the scans first (site/README.md, step 0)")
    return parts


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="provision.py", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("context")
    for name in ("check", "scripts", "flow", "console", "pages"):
        p = sub.add_parser(name)
        p.add_argument("--context", help="a context file other than site/local/context.json")
        if name in ("flow", "console"):
            p.add_argument("--site", help="the site's address, when it differs from site.url in the context")
    p = sub.add_parser("flows")
    p.add_argument("--context", help="a context file other than site/local/context.json")
    p.add_argument("--results-folder-id", required=True, help="the OneDrive id of the results folder")
    p.add_argument("--folder", default=INTAKE_FOLDER, help="the OneDrive folder the intake files go to")
    sub.add_parser("docs")
    args = parser.parse_args(argv)
    lists = load_spec()
    try:
        if args.cmd == "context":
            ctx, notes = merge_context(context_parts())
            problems = check_context(ctx, lists)
            path = _write(CONTEXT, json.dumps(ctx, indent=2, ensure_ascii=False) + "\n")
            print(f"{_show(path)}: {len(ctx.get('products', []))} products, {len(ctx.get('links', []))} links, "
                  f"{len(ctx.get('contacts', []))} contacts, {len(ctx.get('releases', []))} releases, "
                  f"{len(ctx.get('usageTool', {}).get('reportTypes', []))} report types")
            for note in notes:
                print(f"note: {note}")
            for gap in gaps(ctx):
                print(f"gap: {gap}")
            if problems:
                raise Refused("the context is not sound:\n  " + "\n  ".join(problems))
        elif args.cmd == "check":
            ctx = load_context(args.context) if args.context or os.path.exists(CONTEXT) else None
            require_sound(lists, ctx)
            resolved = resolve(lists, ctx)
            print(f"ok: {len(resolved)} lists, {sum(len(e['columns']) for e in resolved)} columns, "
                  f"{sum(len(e['views']) for e in resolved)} views, {sum(len(e.get('seed', [])) for e in resolved)} starter rows"
                  + ("" if ctx else " (no context yet: the structure only)"))
        elif args.cmd == "scripts":
            ctx = load_context(args.context) if args.context or os.path.exists(CONTEXT) else None
            for n, (name, script) in enumerate(scripts(lists, ctx), 1):
                print(_show(_write(os.path.join(OUT, "scripts", f"{n:02d}-{name}.json"), json.dumps(script, indent=2, ensure_ascii=False) + "\n")))
        elif args.cmd in ("flow", "console"):
            ctx = load_context(args.context)
            site = args.site or ctx.get("site", {}).get("url", "")
            if args.cmd == "flow":
                package = provisioning_flow(site, lists, ctx)
                print(_show(_write(os.path.join(OUT, f"{package['name']}.json"), json.dumps(package, indent=2, ensure_ascii=False) + "\n")))
            else:
                print(_show(_write(os.path.join(OUT, "provision.console.js"), console_script(site, lists, ctx))))
        elif args.cmd == "flows":
            ctx = load_context(args.context)
            site = ctx.get("site", {}).get("url", "")
            for package in (intake_out_flow(site, args.folder), intake_back_flow(site, args.results_folder_id), tag_reports_flow(site)):
                print(_show(_write(os.path.join(OUT, f"{package['name']}.json"), json.dumps(package, indent=2, ensure_ascii=False) + "\n")))
        elif args.cmd == "pages":
            ctx = load_context(args.context)
            for rel, text in rendered_files(ctx).items():
                print(_show(_write(os.path.join(OUT, rel), text)))
        elif args.cmd == "docs":
            print(_show(_write(LISTS_MD, docs(lists))))
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
