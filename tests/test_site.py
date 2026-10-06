"""The Data Czars site (`site/`): the list spec and the site scripts made from it, the formatters, the scanned context
and what it becomes (rows, choices, filled-in prompts), the provisioning, intake and report flows, the laptop's intake
runner, the navigation, the page sheets, the site skill, the agents and the artwork. Nothing here reaches SharePoint
or Jira; what only the tenant can prove is `site/README.md`'s table of rows S1 to S14.
"""
from __future__ import annotations
import copy
import glob
import importlib.util
import json
import os
import re
import struct
import uuid
import xml.dom.minidom

import pytest

import koa_contract as KC
from test_build import _check_flowagent_rules

SITE = os.path.join(KC.REPO_ROOT, "site")
SITE_URL = "https://contoso.sharepoint.com/sites/OSP-Data-Czars"


def _load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


P = _load("provision", os.path.join(SITE, "provision.py"))
A = _load("make_assets", os.path.join(SITE, "assets", "make_assets.py"))
I = _load("intake", os.path.join(SITE, "intake", "intake.py"))
LISTS = P.load_spec()
BY_NAME = {entry["name"]: entry for entry in LISTS}
with open(os.path.join(SITE, "site.json"), encoding="utf-8") as _f:
    MANIFEST = json.load(_f)
with open(os.path.join(SITE, "context.example.json"), encoding="utf-8") as _f:
    EXAMPLE = json.load(_f)
PAGES = {page["id"]: page for page in MANIFEST["pages"]}
RESOLVED = {entry["name"]: entry for entry in P.resolve(LISTS, EXAMPLE)}


def _read(rel: str) -> str:
    with open(os.path.join(SITE, rel), encoding="utf-8") as f:
        return f.read()


def _prompt(text: str, after: str) -> str:
    """The first ```text block after the heading or sentence `after`."""
    start = text.index(after)
    m = re.search(r"```text\n(.*?)\n```", text[start:], re.S)
    assert m, f"no ```text block after {after!r}"
    return m.group(1)


def _slug(heading: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")


# ------------------------------------------------------------------------------------ the spec and its scripts


def test_the_list_spec_is_sound_alone_and_with_the_example_context():
    assert P.check(LISTS) == []
    assert P.check(LISTS, EXAMPLE) == []
    assert [e["name"] for e in LISTS][0] == "Products", "Products comes first: Intake looks it up"


def test_the_check_names_what_is_wrong():
    broken = json.loads(json.dumps(LISTS))
    products = broken[0]
    products["columns"].append({"name": "Owner Name", "type": "Text"})
    products["columns"].append({"name": "Size", "type": "Choice", "choices": ["S"], "default": "M"})
    products["views"][0]["fields"].append("Nope")
    next(e for e in broken if e["name"] == "FAQ")["seed"][0]["Topic"] = "Nowhere near"
    next(c for e in broken if e["name"] == "Intake" for c in e["columns"] if c["name"] == "Product")["lookup"] = "Nowhere"
    problems = "\n".join(P.check(broken))
    for words in ("ASCII letters and digits only", "default is not one of the choices", "Nope is not a column",
                  "'Nowhere near' is not a choice of Topic", "looks up Nowhere"):
        assert words in problems


ALLOWED_SUBACTIONS = {
    "setDescription": {"description"},
    "addSPFieldXml": {"schemaXml"},
    "addSPLookupFieldXml": {"schemaXml", "targetListName"},
    "setSPFieldCustomFormatter": {"fieldDisplayName", "formatterJSON"},
    "addSPView": {"name", "viewFields", "query", "rowLimit", "isPaged"},
}


@pytest.mark.parametrize("ctx", [None, EXAMPLE], ids=["structure", "with-context"])
def test_every_site_script_uses_documented_actions_within_the_synchronous_limit(ctx):
    ids = set()
    for name, script in P.scripts(LISTS, ctx):
        assert script["$schema"] == P.SCRIPT_SCHEMA
        assert [a["verb"] for a in script["actions"]] == ["createSPList"]
        action = script["actions"][0]
        assert action["listName"] == name and action["templateType"] in (100, 101)
        assert 1 + len(action["subactions"]) == P.action_count(BY_NAME[name]) <= P.MAX_ACTIONS
        for sub in action["subactions"]:
            required = ALLOWED_SUBACTIONS[sub["verb"]]
            assert required <= set(sub), f"{name}: {sub['verb']} lacks {required - set(sub)}"
            if "schemaXml" in sub:
                field = xml.dom.minidom.parseString(sub["schemaXml"]).documentElement
                internal = field.getAttribute("Name")
                assert field.getAttribute("StaticName") == internal
                assert field.getAttribute("ID") == "{" + str(uuid.uuid5(P.ID_NAMESPACE, f"{name}/{internal}")) + "}"
                ids.add(field.getAttribute("ID"))
            if sub["verb"] == "addSPLookupFieldXml":
                assert sub["targetListName"] in BY_NAME
    assert len(ids) == sum(len(e["columns"]) for e in LISTS), "every column has its own fixed id"


def test_the_scanned_values_join_their_choice_columns_ahead_of_the_defaults():
    category = P.column(list(RESOLVED.values()), "Products", "Category")
    assert category["choices"] == ["Kernel", "Spark", "Data quality", "Other"]
    field = xml.dom.minidom.parseString(P.field_xml("Products", category)).documentElement
    assert [c.firstChild.data for c in field.getElementsByTagName("CHOICE")] == category["choices"]
    assert P.column(list(RESOLVED.values()), "UsageReports", "ReportType")["choices"][:2] == ["Report usage", "Workspace activity"]
    assert P.column(list(RESOLVED.values()), "Releases", "Product")["choices"][:2] == ["Analytics Kernel", "Spark sessions"]
    topics = P.column(list(RESOLVED.values()), "FAQ", "Topic")["choices"]
    assert topics[:3] == ["Analytics Kernel", "Spark sessions", "Table compare"] and "Common errors" in topics
    assert P.column(LISTS, "Products", "Category")["choices"] == ["Other"], "the tracked spec is never changed"


# ------------------------------------------------------------------------------------ the formatters


COLUMN, ROW, TILE = ("https://developer.microsoft.com/json-schemas/sp/v2/" + s + "-formatting.schema.json"
                     for s in ("column", "row", "tile"))


def _references(node) -> set[str]:
    return {m.group(1) for m in re.finditer(r"\[\$([A-Za-z_][A-Za-z0-9_]*)", json.dumps(node))}


def test_every_formatter_names_only_columns_its_list_has_and_declares_its_schema():
    used = set()
    for entry in LISTS:
        known = {c["name"] for c in entry["columns"]} | P.BUILT_IN
        for field, rel in entry.get("formatters", {}).items():
            data = P.formatter(rel)
            assert data["$schema"] == COLUMN, rel
            assert _references(data) <= known, f"{rel} on {entry['name']}: {_references(data) - known}"
            used.add(rel)
        for view in entry["views"]:
            if not view.get("formatter"):
                continue
            data = P.formatter(view["formatter"])
            assert data["$schema"] == (TILE if view.get("type2") == "TILES" else ROW), view["formatter"]
            assert _references(data) <= known, f"{view['formatter']} on {entry['name']}: {_references(data) - known}"
            assert _references(data) <= set(view["fields"]) | P.BUILT_IN, \
                f"{entry['name']} view {view['name']} shows {_references(data) - set(view['fields'])} without selecting it"
            used.add(view["formatter"])
    on_disk = {f"formatting/{os.path.basename(p)}" for p in glob.glob(os.path.join(SITE, "formatting", "*.json"))}
    assert used == on_disk, f"unused formatters: {sorted(on_disk - used)}"


def test_statuses_are_words_with_an_icon_never_colour_alone():
    for rel in ("formatting/product-status.json", "formatting/intake-status.json"):
        data = P.formatter(rel)
        assert data["children"][-1]["txtContent"] == "@currentField", rel
        assert "iconName" in data["children"][0]["attributes"], rel


def test_a_contact_card_opens_the_persons_preferred_way_with_links_formatting_allows():
    card = json.dumps(P.formatter("formatting/contacts-cards.json"))
    methods = P.column(LISTS, "Contacts", "PreferredMethod")["choices"]
    for method in methods:
        assert f"'{method}'" in card or method == "Teams chat", method
    for link in ("https://teams.microsoft.com/l/chat/0/0?users=", "https://teams.microsoft.com/l/call/0/0?users=",
                 "https://teams.microsoft.com/l/meeting/new?subject=", "mailto:"):
        assert link in card
    assert "msteams:" not in card, "list formatting allows only http(s), mailto and tel links"


# ------------------------------------------------------------------------------------ the context


def test_the_example_context_is_sound_and_every_fact_the_pages_use_is_in_it():
    assert P.check_context(EXAMPLE, LISTS) == []
    assert [g for g in P.gaps(EXAMPLE) if g not in EXAMPLE["gaps"]] == []
    assert set(EXAMPLE) <= set(P.SECTIONS)


def test_the_context_check_names_what_is_wrong():
    bad = copy.deepcopy(EXAMPLE)
    bad["contacts"][0]["preferredMethod"] = "Carrier pigeon"
    bad["links"][0]["url"] = "http://jira.contoso.com"
    bad["releases"][0]["product"] = "Nothing we know"
    bad["team"]["triageDays"] = "soon"
    bad["access"][0]["neededFor"] = "Curiosity"
    bad["profiles"][0]["kind"] = "Enormous"
    bad["kernel"]["setupSteps"] = "Do it all at once."
    problems = "\n".join(P.check_context(bad, LISTS))
    for words in ("'Carrier pigeon' is not one of", "is not an https address", "'Nothing we know' is not one of the products",
                  "triageDays: 'soon' is a whole number", "access[1].neededFor: 'Curiosity' is not one of",
                  "profiles[1].kind: 'Enormous' is not one of", "kernel.setupSteps: is a list"):
        assert words in problems


def test_the_parts_merge_first_value_wins_and_lists_join_once_per_identity():
    operator = {"team": {"triageDays": "2"}, "site": {"url": SITE_URL}}
    scan = {"team": {"triageDays": "3", "mission": "M"}, "products": [{"name": "A"}, {"name": "B"}]}
    again = {"products": [{"name": "a"}, {"name": "C"}], "gaps": ["one"], "nonsense": {}}
    ctx, notes = P.merge_context([("00-operator.json", operator), ("data-czars.json", scan), ("usage_tool.json", again)])
    assert ctx["team"] == {"triageDays": "2", "mission": "M"}
    assert [p["name"] for p in ctx["products"]] == ["A", "B", "C"]
    assert ctx["gaps"] == ["one"]
    assert any("kept '2'" in n for n in notes) and any("nonsense" in n for n in notes) and any("already there" in n for n in notes)


def test_the_context_becomes_rows_without_a_person_or_a_lookup():
    seeded = {name: entry["seed"] for name, entry in RESOLVED.items()}
    products = seeded["Products"]
    assert [r["Title"] for r in products] == ["Analytics Kernel", "Spark sessions", "Table compare"]
    assert products[0]["DocsLink"] == {"url": "https://confluence.contoso.com/display/DCZ/Analytics+Kernel", "desc": "Confluence"}
    assert seeded["Releases"][0]["Title"] == "Spark sessions 2026.09" and seeded["Releases"][0]["ReleasedOn"] == "2026-09-30"
    access = seeded["Access"]
    assert [r["Title"] for r in access] == [a["name"] for a in EXAMPLE["access"]]
    assert access[0]["RequestLink"]["url"] == EXAMPLE["access"][0]["request"]["url"] and access[-1]["NeededFor"] == "Contributing code"
    profiles = seeded["SparkProfiles"]
    assert [r["Title"] for r in profiles] == ["small", "medium", "large", "wide-shuffle"]
    assert profiles[-1]["Kind"] == "Specialized" and profiles[0]["ExecutorMemory"] == "4g" and profiles[0]["SortOrder"] == 10
    assert set(r for row in access + profiles for r in row) <= _columns("Access") | _columns("SparkProfiles")
    assert [r["Email"] for r in seeded["Contacts"]] == [c["email"] for c in EXAMPLE["contacts"]]
    assert [r["Title"] for r in seeded["Links"]] == [link["title"] for link in EXAMPLE["links"]]
    assert seeded["FAQ"][-1]["Title"] == EXAMPLE["faq"][-1]["question"] and seeded["FAQ"][-1]["Topic"] == "Common errors"
    triage = next(r for r in seeded["FAQ"] if r["Title"] == "What happens after I submit?")
    assert "within 3 business days" in triage["Answer"], "a tracked row's fact is filled in from the context"


def test_tracked_starter_rows_carry_no_internal_fact():
    for entry in LISTS:
        for row in entry.get("seed", []):
            text = json.dumps(row)
            assert "://" not in text and not re.search(r"[\w.+-]+@[\w-]+\.\w", text), f"{entry['name']}: {row['Title']}"
    for name in ("Products", "Access", "SparkProfiles", "Contacts", "Links"):
        assert not BY_NAME[name]["seed"], f"{name}: its rows come only from the context"


def test_a_page_fact_missing_from_the_context_is_refused_by_name():
    thin = copy.deepcopy(EXAMPLE)
    thin["team"]["triageDays"] = ""
    with pytest.raises(P.Refused, match="team.triageDays"):
        P.rendered_files(thin)
    assert "team.triageDays: used by the pages, still empty" in P.gaps(thin)


def test_every_page_and_agent_file_renders_with_nothing_left_unfilled():
    rendered = P.rendered_files(EXAMPLE)
    assert {k for k in rendered if k.startswith("pages/")} == {p["file"] for p in MANIFEST["pages"]}
    assert {k for k in rendered if k.startswith("agents/")} == {
        "agents/" + os.path.basename(p) for p in glob.glob(os.path.join(SITE, "agents", "*"))}
    for rel, text in rendered.items():
        assert "{{" not in text and "}}" not in text, rel
    assert EXAMPLE["kernel"]["name"] not in _read("pages/get-started.md"), "the tracked sheet holds no scanned fact"
    assert EXAMPLE["team"]["mission"] in rendered["pages/home.md"]
    start = rendered["pages/get-started.md"]
    steps = "\n".join(f"   {n}. {step}" for n, step in enumerate(EXAMPLE["kernel"]["setupSteps"], 1))
    assert steps in start, "the setup steps are a numbered list at the prompt's indent"
    assert EXAMPLE["kernel"]["firstSession"] in start and "pandas, matplotlib and the team's" in start


# ------------------------------------------------------------------------------------ provisioning


def test_lists_md_is_what_the_spec_generates():
    assert _read("LISTS.md") == P.docs(LISTS), "run: python site/provision.py docs"


def _check_payloads(actions: dict, ctx: dict) -> None:
    items = actions["Scripts"]["inputs"]
    assert [i["list"] for i in items] == [e["name"] for e in LISTS]
    for item, (name, script) in zip(items, P.scripts(LISTS, ctx)):
        assert json.loads(json.loads(item["body"])["script"]) == script
    seeded = {s["list"]: s["rows"] for s in actions["Seed"]["inputs"]}
    assert set(seeded) == {name for name, e in RESOLVED.items() if e["seed"]}
    for name, rows in seeded.items():
        assert [r["title"] for r in rows] == [row["Title"] for row in RESOLVED[name]["seed"]]
        for r in rows:
            assert json.loads(r["body"])["__metadata"]["type"] == f"SP.Data.{name}ListItem"
    # A workflow string that starts with @ is an expression and @{ anywhere is interpolation: the payloads must be
    # neither, or the flow would evaluate a formatter's text instead of sending it.
    for body in [i["body"] for i in items] + [r["body"] for rows in seeded.values() for r in rows]:
        assert not body.startswith("@") and "@{" not in body


def test_the_provisioning_flow_keeps_flowagents_rules_and_carries_every_script_and_row():
    package = P.provisioning_flow(SITE_URL, LISTS, EXAMPLE)
    _check_flowagent_rules(package)
    actions = package["definition"]["actions"]
    _check_payloads(actions, EXAMPLE)
    apply = actions["For_each_script"]["actions"]["Apply_script"]["inputs"]["parameters"]
    assert apply["parameters/uri"] == P.EXECUTE and apply["parameters/method"] == "POST" and apply["dataset"] == SITE_URL
    assert "contoso" not in json.dumps(P.scripts(LISTS)), "the structure's scripts carry no site address"


def test_the_console_script_does_what_the_flow_does():
    js = P.console_script(SITE_URL, LISTS, EXAMPLE)
    assert P.EXECUTE in js and "X-RequestDigest" in js and "_api/contextinfo" in js
    for entry in LISTS:
        assert f'"list": "{entry["name"]}"' in js
    assert js.count("{") == js.count("}") and js.count("(") == js.count(")")


@pytest.mark.parametrize("site", ["", "http://contoso.sharepoint.com/sites/x", "https://example.com/sites/x"])
def test_provisioning_refuses_an_address_that_is_not_a_sharepoint_site(site):
    with pytest.raises(P.Refused):
        P.provisioning_flow(site, LISTS, EXAMPLE)


# ------------------------------------------------------------------------------------ intake and reports flows


def _columns(list_name: str) -> set[str]:
    return {c["name"] for c in BY_NAME[list_name]["columns"]} | P.BUILT_IN


def test_the_intake_and_report_flows_keep_flowagents_rules_and_name_real_columns():
    out = P.intake_out_flow(SITE_URL)
    back = P.intake_back_flow(SITE_URL, "01RESULTSFOLDER")
    tags = P.tag_reports_flow(SITE_URL)
    for package in (out, back, tags):
        _check_flowagent_rules(package)
    sent = {v.split("/")[0] for k, v in P.INTAKE_FIELDS.items() if k != "kind" and not v.startswith("{")}
    assert sent <= _columns("Intake"), sent - _columns("Intake")
    assert out["definition"]["actions"]["Create_intake_file"]["inputs"]["parameters"]["folderPath"] == "/DataCzars/intake"
    assert back["definition"]["triggers"]["When_a_result_arrives"]["inputs"]["parameters"]["folderId"] == "01RESULTSFOLDER"
    tag = json.dumps(tags)
    for column in ("ReportType", "PeriodStart", "PeriodType", "ReportStatus"):
        assert f'\\"{column}\\"' in tag and column in _columns("UsageReports")
    with pytest.raises(P.Refused):
        P.intake_back_flow(SITE_URL, "")


def test_a_synced_library_has_no_required_column():
    assert not [c["name"] for c in BY_NAME["UsageReports"]["columns"] if c.get("required")], \
        "a synced library with a required column goes read-only"


# ------------------------------------------------------------------------------------ the laptop's intake runner


INTAKE_ROW = {"kind": "intake", "id": 12, "title": "Session fails on Mondays", "type": "Report an issue",
       "product": "Spark sessions", "details": "The 6 AM job cannot start Spark.", "impact": "Blocking my work",
       "affectedTeam": "Finance reporting", "neededBy": "", "requester": "jordan.sample@contoso.com",
       "requesterName": "Jordan Sample", "created": "2026-10-06T12:00:00Z", "link": f"{SITE_URL}/Lists/Intake/12_.000"}


def test_an_intake_row_becomes_the_ticket_the_projects_facts_say():
    t = I.ticket(INTAKE_ROW, EXAMPLE)
    assert t == {"summary": "Issue (Spark sessions): Session fails on Mondays", "type": "Bug", "project": "DCZ",
                 "components": ["Spark"], "labels": ["sharepoint-intake"],
                 "description": t["description"]}
    assert "Raised by Jordan Sample <jordan.sample@contoso.com> on the Data Czars site, intake #12." in t["description"]
    assert I.ticket(dict(INTAKE_ROW, type="Request access", product=""), EXAMPLE)["type"] == "Task"
    args = I.create_args(t, "body.txt", dry_run=True)
    assert args[:2] == ["ad-jira", "create"] and args[-1] == "--dry-run" and ["--component", "Spark"] == args[10:12]


def _drop(folder, row):
    os.makedirs(os.path.join(folder, "intake"), exist_ok=True)
    with open(os.path.join(folder, "intake", f"intake-{row['id']}.json"), "w", encoding="utf-8") as f:
        json.dump(row, f)


def test_filing_writes_a_result_the_flow_merges_and_never_files_twice(tmp_path, monkeypatch):
    folder = str(tmp_path)
    _drop(folder, INTAKE_ROW)
    calls = []
    monkeypatch.setattr(I, "run", lambda args: (calls.append(args) or (0, "meta:\n  ok: true\n  key: DCZ-41\n")))
    assert I.file_rows(folder, EXAMPLE, None, dry_run=False) == ["#12: DCZ-41"]
    results = glob.glob(os.path.join(folder, "results", "12-*.json"))
    merge = json.load(open(results[0], encoding="utf-8"))
    assert merge["id"] == 12 and merge["merge"]["JiraKey"] == "DCZ-41" and merge["merge"]["Status"] == "Sent to Jira"
    assert merge["merge"]["JiraLink"]["Url"] == "https://jira.contoso.com/browse/DCZ-41"
    assert merge["merge"]["__metadata"]["type"] == "SP.Data.IntakeListItem"
    assert set(merge["merge"]) - {"__metadata"} <= _columns("Intake")
    assert I.pending(folder) == [] and I.file_rows(folder, EXAMPLE, None, dry_run=False) == [] and len(calls) == 1


def test_a_refused_or_dry_run_filing_writes_nothing(tmp_path, monkeypatch):
    folder = str(tmp_path)
    _drop(folder, INTAKE_ROW)
    monkeypatch.setattr(I, "run", lambda args: (2, "meta:\n  ok: false\n  refused: denied\n"))
    assert I.file_rows(folder, EXAMPLE, ["12"], dry_run=False)[0].startswith("#12: not filed")
    monkeypatch.setattr(I, "run", lambda args: (0, "meta:\n  dry_run: true\n"))
    assert I.file_rows(folder, EXAMPLE, ["12"], dry_run=True)[0].startswith("#12: would file Bug in DCZ")
    assert not os.path.exists(os.path.join(folder, "results")) and [r["id"] for r in I.pending(folder)] == [12]


def test_sync_follows_jiras_status_category_and_leaves_closed_rows_alone(tmp_path, monkeypatch):
    folder = str(tmp_path)
    I._write(os.path.join(folder, "ledger.json"), {"12": {"key": "DCZ-41", "status": "Sent to Jira"},
                                                     "13": {"key": "DCZ-42", "status": "Done"}})
    asked = []
    monkeypatch.setattr(I, "run", lambda args: (asked.append(args[-1]) or (0, "meta:\n  ok: true\n  status: \"In Progress\"\n  status_category: indeterminate\n")))
    assert I.sync(folder, EXAMPLE) == ["#12 DCZ-41: In Progress"]
    assert asked == ["DCZ-41"] and I.ledger(folder)["12"]["status"] == "In progress"
    assert I.sync(folder, EXAMPLE) == [], "an unchanged status writes nothing"


# ------------------------------------------------------------------------------------ navigation and pages


def _nav_links():
    for item in MANIFEST["navigation"]:
        yield item
        for group in item.get("groups", []):
            for link in group["links"]:
                yield link


def test_navigation_reaches_only_pages_that_exist_and_anchors_their_sheets_create():
    for link in _nav_links():
        if "url" in link:
            continue
        page = PAGES[link["page"]]
        if "anchor" in link:
            prompt = _prompt(_read(page["file"]), "## Build it with Copilot")
            headings = {_slug(h) for h in re.findall(r'[Hh]eading "([^"]+)"', prompt)}
            assert link["anchor"] in headings, f"{link['label']}: no heading makes #{link['anchor']} on {page['file']}"


def test_the_team_links_are_targeted():
    help_ = next(item for item in MANIFEST["navigation"] if item["label"] == "Get help")
    team = next(g for g in help_["groups"] if g["heading"] == "For the team")
    assert team.get("members") and all(link.get("members") for link in team["links"])


def test_the_navigation_prompt_in_the_build_sheet_matches_the_manifest():
    prompt = _prompt(_read("README.md"), "## 4. The navigation")
    for item in MANIFEST["navigation"]:
        assert f"{item['label']}: {PAGES[item['page']]['url'].split('/')[-1]}" in prompt
        for group in item.get("groups", []):
            assert f"  {group['heading']}: " in prompt
            for link in group["links"]:
                assert link["label"] in prompt
                if "anchor" in link:
                    assert f"#{link['anchor']}" in prompt


SHEET_PARTS = ("## Build it with Copilot", "## Sections", "## Words", "## Finish by hand", "## Check")


@pytest.mark.parametrize("page_id", sorted(PAGES))
def test_every_page_sheet_has_its_parts_and_names_the_views_it_uses(page_id):
    page = PAGES[page_id]
    text = _read(page["file"])
    assert text.startswith(f"# {page['title']}\n")
    assert f"`{page['url']}`" in text
    positions = [text.index(part) for part in SHEET_PARTS]
    assert positions == sorted(positions), page["file"]
    prompt = _prompt(text, "## Build it with Copilot")
    assert "Propose the layout first and wait for my go-ahead." in prompt
    assert "full-width" not in prompt.lower() and "flexible" not in prompt.lower()
    for used in page["uses"]:
        list_name, view = used.split("/")
        assert view in [v["name"] for v in BY_NAME[list_name]["views"]], used
        assert f"`{list_name}`, view `{view}`" in text, f"{page['file']} does not name {used}"


def test_every_page_in_the_manifest_has_a_sheet_and_every_sheet_a_page():
    on_disk = {os.path.relpath(p, SITE).replace(os.sep, "/") for p in glob.glob(os.path.join(SITE, "pages", "*.md"))}
    assert on_disk == {page["file"] for page in MANIFEST["pages"]}


def test_every_asset_the_site_names_exists():
    texts = [_read(p["file"]) for p in MANIFEST["pages"]] + [json.dumps(MANIFEST), _read("README.md")]
    named = {m for text in texts for m in re.findall(r"(?:assets/)?([a-z0-9-]+\.png)", text)}
    assert named, "the sheets name their images"
    for name in named:
        assert os.path.exists(os.path.join(SITE, "assets", name)), name


# ------------------------------------------------------------------------------------ skill, agents, prompts


def test_the_site_skill_knows_every_list_and_names_itself():
    text = _read(MANIFEST["skill"])
    front = re.match(r"---\nname: (\S+)\ndescription: (.+?)\n---\n", text, re.S)
    assert front and front.group(1) == os.path.basename(os.path.dirname(MANIFEST["skill"]))
    table = text[text.index("## Lists"):]
    for entry in LISTS:
        assert re.search(rf"^\| {entry['name']}\b", table, re.M), entry["name"]
        for view in re.findall(r"^\| " + entry["name"] + r"\b[^|]*\|[^|]*\| ([^|]+) \|", table, re.M)[0].split(", "):
            assert view.split(" (")[0] in [v["name"] for v in entry["views"]], f"{entry['name']}: {view}"


def test_ask_the_czars_reads_the_sites_lists_but_never_intake():
    text = _read("agents/ask-the-czars.md")
    sources = text[text.index("## Sources"):text.index("## Instructions")]
    for name in BY_NAME:
        if name != "Intake":
            assert name in sources, name
    assert sources.count("Intake") == 1 and "Not `Intake`" in sources
    instructions = _prompt(text, "## Instructions")
    assert "Never guess" in instructions and "Cite" in instructions and "You cannot file anything yourself" in instructions


def test_czars_desk_acts_only_as_the_person_and_only_on_confirmation():
    text = _read("agents/czars-desk.md")
    assert "end-user credentials" in " ".join(text.split())
    instructions = _prompt(text, "## Instructions")
    assert "Never file anything the person did not confirm" in instructions
    assert "never change or delete a row" in instructions


def test_the_agents_readme_names_every_agent_file():
    readme = _read(MANIFEST["agents"])
    for path in glob.glob(os.path.join(SITE, "agents", "*.md")):
        name = os.path.basename(path)
        if name != "README.md":
            assert f"`{name}`" in readme, name


def test_the_scan_prompts_read_only_and_write_only_their_own_context_file():
    folder = os.path.join(KC.REPO_ROOT, ".github", "prompts")
    scans = {"czars-scan-data-czars.prompt.md": "data-czars.json", "czars-scan-usage-tool.prompt.md": "usage_tool.json",
             "czars-scan-fleet.prompt.md": "fleet.json"}
    for name, out in scans.items():
        text = open(os.path.join(folder, name), encoding="utf-8").read()
        assert text.startswith("---\ndescription: ")
        assert f"site/local/context/{out}" in text and "python site/provision.py context" in text
        assert "Read only" in text
    sections = {"data-czars.json": {"team", "jira", "kernel", "products", "profiles", "access", "links", "releases", "faq"},
                "usage_tool.json": {"usageTool", "products", "links", "releases", "faq"}, "fleet.json": {"fleet"}}
    for name, keys in sections.items():
        assert keys <= set(P.SECTIONS), name
    org = _prompt(_read("prompts/m365-org-facts.md"), "Fill in the two")
    shape = json.loads(org[org.index("{"):org.index("Rules:")].strip())
    assert set(shape) <= set(P.SECTIONS) and set(shape["contacts"][0]) == set(EXAMPLE["contacts"][0])
    wiki = _prompt(_read("prompts/confluence-page-facts.md"), "Fill in the bracketed line")
    shape = json.loads(wiki[wiki.index("{"):wiki.index("Rules:")].strip())
    assert set(shape) <= set(P.SECTIONS)
    for key in ("access", "profiles", "faq", "links"):
        assert set(shape[key][0]) == set(EXAMPLE[key][0]), key
    assert set(shape["kernel"]) <= set(EXAMPLE["kernel"])
    scan = {"kernel": {"name": "From the code"}, "profiles": [{"name": "small", "executors": "2"}]}
    page = {"kernel": {"name": "From the page", "setupSteps": ["Open JupyterHub."]}, "profiles": [{"name": "small", "executors": "3"}]}
    parts = sorted([("wiki-kernel.json", page), ("data-czars.json", scan)])
    ctx, _ = P.merge_context(parts)
    assert ctx["kernel"] == {"name": "From the code", "setupSteps": ["Open JupyterHub."]} and ctx["profiles"][0]["executors"] == "2", \
        "the Confluence parts merge after the scans: the repository wins, the page fills what it leaves out"
    assert "wiki-<page>.json" in _read("README.md") and "wiki-<page>.json" in _read("prompts/confluence-page-facts.md")


# ------------------------------------------------------------------------------------ the artwork


def _png_size(path: str) -> tuple[int, int]:
    with open(path, "rb") as f:
        head = f.read(24)
    assert head[:8] == b"\x89PNG\r\n\x1a\n", path
    return struct.unpack(">II", head[16:24])


def test_the_svgs_are_what_the_script_draws_and_every_png_matches_its_svg():
    drawn = A.art(A.TEAL)
    svgs = {os.path.basename(p)[:-4] for p in glob.glob(os.path.join(SITE, "assets", "*.svg"))}
    pngs = {os.path.basename(p)[:-4] for p in glob.glob(os.path.join(SITE, "assets", "*.png"))}
    assert svgs == set(drawn) == pngs
    for name, text in drawn.items():
        assert _read(f"assets/{name}.svg") == text, f"run: python site/assets/make_assets.py ({name})"
        assert _png_size(os.path.join(SITE, "assets", f"{name}.png")) == A.size(text), name


def _luminance(hex_colour: str) -> float:
    def channel(v: int) -> float:
        c = v / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = A._rgb(hex_colour)
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def test_the_theme_contrast_the_design_claims_holds():
    ratio = (1.05) / (_luminance(A.TEAL) + 0.05)
    assert ratio >= 4.5
    assert f"is {ratio:.1f}:1" in _read("DESIGN.md")


# ------------------------------------------------------------------------------------ public repository, private facts


def _site_text_files():
    paths = glob.glob(os.path.join(SITE, "**", "*"), recursive=True)
    paths += glob.glob(os.path.join(KC.REPO_ROOT, ".github", "prompts", "czars-*.prompt.md"))
    paths.append(os.path.join(KC.REPO_ROOT, ".github", "skills", "build-czars-site", "SKILL.md"))
    for path in paths:
        rel = os.path.relpath(path, SITE).replace(os.sep, "/")
        if rel.startswith(("out/", "local/")) or not path.endswith((".md", ".json", ".py", ".svg", ".code-workspace")):
            continue
        yield path


def test_the_site_files_are_utf8_lf_without_trailing_whitespace():
    checked = 0
    for path in _site_text_files():
        raw = open(path, "rb").read()
        text = raw.decode("utf-8")
        rel = os.path.relpath(path, KC.REPO_ROOT)
        assert b"\r" not in raw and not raw.startswith(b"\xef\xbb\xbf"), rel
        assert text.endswith("\n"), f"{rel}: no final newline"
        for n, line in enumerate(text.split("\n"), 1):
            assert line == line.rstrip(), f"{rel}:{n}: trailing whitespace"
        checked += 1
    assert checked >= 45


#: The only hosts a tracked site file may name: Microsoft's and GitHub's public pages, the made-up Contoso tenant of
#: the example context, and the `<tenant>` placeholder. A bank address in a tracked file is a fact leaking out.
PUBLIC_HOSTS = {"github.com", "developer.microsoft.com", "schema.management.azure.com", "teams.microsoft.com",
                "www.w3.org", "contoso.sharepoint.com", "jira.contoso.com", "confluence.contoso.com",
                "bitbucket.contoso.com", "access.contoso.com", "<tenant>.sharepoint.com"}


def test_tracked_site_files_name_no_internal_host_or_mailbox():
    for path in _site_text_files():
        text = open(path, encoding="utf-8").read()
        rel = os.path.relpath(path, KC.REPO_ROOT)
        for host in re.findall(r"https?://(<tenant>\.sharepoint\.com|[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)", text):
            assert host in PUBLIC_HOSTS, f"{rel}: {host}"
        for mailbox in re.findall(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+\.[A-Za-z.]{2,})", text):
            assert mailbox == "contoso.com", f"{rel}: a mailbox at {mailbox}"


def test_git_ignores_the_scanned_facts_and_everything_made_from_them():
    with open(os.path.join(KC.REPO_ROOT, ".gitignore"), encoding="utf-8") as f:
        ignored = f.read().split("\n")
    assert "site/local/" in ignored and "site/out/" in ignored
