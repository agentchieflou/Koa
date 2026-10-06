"""The Data Czars site (`site/`): the list spec and the site scripts made from it, the formatters, the provisioning
flow and console script, the navigation, the page sheets, the site skill, the agent and the artwork. Nothing here can
reach SharePoint; what only the tenant can prove is `site/README.md`'s table of rows S1 to S10.
"""
from __future__ import annotations
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
LISTS = P.load_spec()
BY_NAME = {entry["name"]: entry for entry in LISTS}
with open(os.path.join(SITE, "site.json"), encoding="utf-8") as _f:
    MANIFEST = json.load(_f)
PAGES = {page["id"]: page for page in MANIFEST["pages"]}


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


def test_the_list_spec_is_sound():
    assert P.check(LISTS) == []
    assert [e["name"] for e in LISTS][:1] == ["Tools"], "Tools comes first: every lookup targets it"


def test_the_check_names_what_is_wrong():
    broken = json.loads(json.dumps(LISTS))
    tools = broken[0]
    tools["columns"].append({"name": "Owner Name", "type": "Text"})
    tools["columns"].append({"name": "Size", "type": "Choice", "choices": ["S"], "default": "M"})
    tools["views"][0]["fields"].append("Nope")
    tools["seed"][0]["Status"] = "Fine"
    broken[1]["columns"][1]["lookup"] = "Nowhere"
    problems = "\n".join(P.check(broken))
    for words in ("ASCII letters and digits only", "default is not one of the choices", "Nope is not a column",
                  "'Fine' is not a choice of Status", "looks up Nowhere"):
        assert words in problems


ALLOWED_SUBACTIONS = {
    "setDescription": {"description"},
    "addSPFieldXml": {"schemaXml"},
    "addSPLookupFieldXml": {"schemaXml", "targetListName"},
    "setSPFieldCustomFormatter": {"fieldDisplayName", "formatterJSON"},
    "addSPView": {"name", "viewFields", "query", "rowLimit", "isPaged"},
}


def test_every_site_script_uses_documented_actions_within_the_synchronous_limit():
    ids = set()
    for name, script in P.scripts(LISTS):
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


def test_choices_and_defaults_reach_the_field_xml():
    status = next(c for c in BY_NAME["Tools"]["columns"] if c["name"] == "Status")
    field = xml.dom.minidom.parseString(P.field_xml("Tools", status)).documentElement
    assert [c.firstChild.data for c in field.getElementsByTagName("CHOICE")] == status["choices"]
    assert field.getElementsByTagName("Default")[0].firstChild.data == "Operational"
    assert field.getAttribute("Required") == "TRUE" and field.getAttribute("Type") == "Choice"


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
    for rel in ("formatting/tool-status.json", "formatting/request-status.json", "formatting/decision-status.json"):
        data = P.formatter(rel)
        assert data["children"][-1]["txtContent"] == "@currentField", rel
        assert "iconName" in data["children"][0]["attributes"], rel


# ------------------------------------------------------------------------------------ provisioning


def test_lists_md_is_what_the_spec_generates():
    assert _read("LISTS.md") == P.docs(LISTS), "run: python site/provision.py docs"


def test_the_provisioning_flow_keeps_flowagents_rules_and_carries_every_script_and_row():
    package = P.provisioning_flow(SITE_URL, LISTS)
    _check_flowagent_rules(package)
    actions = package["definition"]["actions"]
    items = actions["Scripts"]["inputs"]
    assert [i["list"] for i in items] == [e["name"] for e in LISTS]
    for item, (name, script) in zip(items, P.scripts(LISTS)):
        assert json.loads(json.loads(item["body"])["script"]) == script
    apply = actions["For_each_script"]["actions"]["Apply_script"]["inputs"]["parameters"]
    assert apply["parameters/uri"] == P.EXECUTE and apply["parameters/method"] == "POST"
    assert apply["dataset"] == SITE_URL
    seeded = {s["list"]: s["rows"] for s in actions["Seed"]["inputs"]}
    assert set(seeded) == {e["name"] for e in LISTS if e.get("seed")}
    for name, rows in seeded.items():
        assert [r["title"] for r in rows] == [row["Title"] for row in BY_NAME[name]["seed"]]
        for r in rows:
            body = json.loads(r["body"])
            assert body["__metadata"]["type"] == f"SP.Data.{name}ListItem"
    assert "contoso" not in json.dumps(P.scripts(LISTS)), "the scripts carry no site address"
    # A workflow string that starts with @ is an expression and @{ anywhere is interpolation: the payloads must be
    # neither, or the flow would evaluate a formatter's text instead of sending it.
    for body in [i["body"] for i in items] + [r["body"] for rows in seeded.values() for r in rows]:
        assert not body.startswith("@") and "@{" not in body


def test_the_console_script_does_what_the_flow_does():
    js = P.console_script(SITE_URL, LISTS)
    assert P.EXECUTE in js and "X-RequestDigest" in js and "_api/contextinfo" in js
    for entry in LISTS:
        assert f'"list": "{entry["name"]}"' in js
    assert js.count("{") == js.count("}") and js.count("(") == js.count(")")


@pytest.mark.parametrize("site", ["", "http://contoso.sharepoint.com/sites/x", "https://example.com/sites/x"])
def test_provisioning_refuses_an_address_that_is_not_a_sharepoint_site(site):
    with pytest.raises(P.Refused):
        P.provisioning_flow(site, LISTS)


def test_starter_rows_name_no_person_and_no_published_number():
    for entry in LISTS:
        for row in entry.get("seed", []):
            assert "@" not in json.dumps(row), row["Title"]
    for row in BY_NAME["Metrics"]["seed"]:
        assert row["MetricValue"] == "[N]", "a number arrives with its method, from the flow, never typed into the spec"


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


def test_the_members_links_are_targeted():
    team = next(item for item in MANIFEST["navigation"] if item["label"] == "Team")
    members = next(g for g in team["groups"] if g["heading"] == "Members")
    assert members.get("members") and all(link.get("members") for link in members["links"])


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


# ------------------------------------------------------------------------------------ skill and agent


def test_the_site_skill_knows_every_list_and_names_itself():
    text = _read(MANIFEST["skill"])
    front = re.match(r"---\nname: (\S+)\ndescription: (.+?)\n---\n", text, re.S)
    assert front and front.group(1) == os.path.basename(os.path.dirname(MANIFEST["skill"]))
    table = text[text.index("## Lists"):]
    for entry in LISTS:
        assert re.search(rf"^\| {entry['name']}\b", table, re.M), entry["name"]
        for view in re.findall(r"^\| " + entry["name"] + r"\b[^|]*\|[^|]*\| ([^|]+) \|", table, re.M)[0].split(", "):
            assert view.split(" (")[0] in [v["name"] for v in entry["views"]], f"{entry['name']}: {view}"


def test_the_agent_reads_the_sites_lists_but_never_the_requests():
    text = _read(MANIFEST["agent"])
    sources = text[text.index("## Sources"):text.index("## Instructions")]
    for entry in LISTS:
        if entry["name"] in ("Requests", "Onboarding"):
            continue
        assert entry["name"] in sources, entry["name"]
    assert sources.count("Requests") == 1 and "Not Requests" in sources
    instructions = _prompt(text, "## Instructions")
    assert "Never guess" in instructions and "Cite" in instructions


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


# ------------------------------------------------------------------------------------ bytes


def _site_text_files():
    paths = glob.glob(os.path.join(SITE, "**", "*"), recursive=True)
    paths.append(os.path.join(KC.REPO_ROOT, ".github", "skills", "build-czars-site", "SKILL.md"))
    for path in paths:
        if os.sep + "out" + os.sep in path or not path.endswith((".md", ".json", ".py", ".svg")):
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
    assert checked >= 40


def test_no_tenant_address_or_mailbox_in_the_site_sources():
    for path in _site_text_files():
        text = open(path, encoding="utf-8").read()
        rel = os.path.relpath(path, KC.REPO_ROOT)
        for m in re.finditer(r"([A-Za-z0-9<>-]+)\.sharepoint\.com", text):
            assert m.group(1) in ("<tenant>", "contoso"), f"{rel}: {m.group(0)}"
        assert not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}", text), f"{rel} carries a mailbox"
