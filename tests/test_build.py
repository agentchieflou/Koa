"""The Copilot build (`build/`): what `build/prepare.py` hands the FlowAgent and Canvas Authoring MCP servers, and the
instruction files that tell an agent when to run it. An agent follows these files literally, so a step that names a
command, a file or a count that does not exist is a build that stops halfway on the operator's laptop.
"""
from __future__ import annotations
import glob
import importlib.util
import json
import os
import re
import shutil

import pytest

import koa_contract as KC
from test_mobile_powerapp import COLUMNS, LISTS

BUILD = os.path.join(KC.REPO_ROOT, "build")
CONFIG = {"environment": "Default-00000000-0000-0000-0000-000000000000", "siteUrl": "https://tenant.sharepoint.com/sites/Fleet",
          "operator": "op@tenant.example", "outboxFolderPath": "/FleetAgent/outbox", "inboxFolderPath": "/FleetAgent/inbox",
          "appId": "6fc3e3d1-292b-4281-8826-577f78512e56", "outboxFolderId": "01FOLDERIDFOROUTBOX"}


def _prepare():
    spec = importlib.util.spec_from_file_location("prepare", os.path.join(BUILD, "prepare.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


P = _prepare()


def _actions_with_parents(node, parent="<root>"):
    """(name, action, sibling names) for every action, scope by scope, so runAfter can be checked per scope."""
    if isinstance(node, dict):
        for key in ("actions",):
            if isinstance(node.get(key), dict):
                siblings = set(node[key])
                for name, action in node[key].items():
                    yield name, action, siblings
                    yield from _actions_with_parents(action, name)
        for key, value in node.items():
            if key != "actions":
                yield from _actions_with_parents(value, parent)
    elif isinstance(node, list):
        for value in node:
            yield from _actions_with_parents(value, parent)


def _check_flowagent_rules(package: dict):
    """FlowAgent's validator rules (power-automate plugin, references/definition-reference.md)."""
    definition = package["definition"]
    assert {"$authentication", "$connections"} == set(definition["parameters"]), definition["parameters"].keys()
    text = json.dumps(definition)
    assert "_comment" not in text and "fleet_" not in text
    for name, action, siblings in _actions_with_parents(definition):
        assert set(action.get("runAfter", {})) <= siblings, f"{name} runs after an action outside its scope"
        if action.get("type") == "OpenApiConnection":
            assert "authentication" not in action["inputs"], f"{name}: FlowAgent injects authentication"
            assert action["inputs"]["host"]["connectionName"] in package["connectors"], name
        assert action.get("type") != "ApiConnection", name
    assert set(package["connectionRefsTemplate"]) == set(package["connectors"])
    for key, ref in package["connectionRefsTemplate"].items():
        assert ref["source"] == package["connectors"][key] and ref["id"].endswith("/" + key)


# ------------------------------------------------------------------------------------ the lists


def test_the_provisioning_spec_is_the_contracts_columns_less_what_sharepoint_already_has():
    spec = P.provisioning_spec()
    assert [entry["list"] for entry in spec] == list(LISTS)
    for entry in spec:
        want = [c for c in COLUMNS[entry["list"]] if c not in ("Title", "Created")]
        assert [c["name"] for c in entry["columns"]] == want, entry["list"]
        created = json.loads(entry["create"])
        assert created["Title"] == entry["list"] and created["BaseTemplate"] == 100


def test_multi_line_columns_are_the_data_readmes_and_every_column_is_plain_text_under_its_own_internal_name():
    spec = {e["list"]: e for e in P.provisioning_spec()}
    multi = {(t, c["name"]) for t, e in spec.items() for c in e["columns"] if c["multi"]}
    assert multi == {("FleetAttention", "Says"), ("FleetAttention", "ApprovalsJson"), ("FleetAttention", "QuestionsJson"),
                     ("FleetApprovals", "PayloadPreview"), ("FleetDecisions", "Message"),
                     ("FleetDecisions", "AnswersJson"), ("FleetNotifications", "Body")}
    for table, entry in spec.items():
        for column in entry["columns"]:
            params = json.loads(column["body"])["parameters"]
            xml = params["SchemaXml"]
            assert '"' not in xml, "single quotes only: the XML sits inside a JSON string"
            assert f"Name='{column['name']}'" in xml and f"StaticName='{column['name']}'" in xml
            assert ("Type='Note'" in xml and "RichText='FALSE'" in xml) if column["multi"] else "Type='Text'" in xml
            assert params["Options"] & 8, "AddFieldInternalNameHint keeps the internal name the flows and app use"


def test_the_provisioning_flow_follows_flowagents_rules_and_only_creates_what_is_missing():
    package = P.provisioning_flow(CONFIG)
    _check_flowagent_rules(package)
    assert package["connectors"] == {"shared_sharepointonline": "Embedded"}
    definition = package["definition"]
    assert definition["triggers"]["manual"]["kind"] == "Button"
    actions = {name: action for name, action, _ in _actions_with_parents(definition)}
    for create, guard in (("Create_list", "List_is_missing"), ("Create_column", "Column_is_missing")):
        [clause] = actions[guard]["expression"]["and"]
        assert create in actions[guard]["actions"] and set(clause["not"]) == {"contains"}
    for name in ("For_each_list", "For_each_column"):
        assert actions[name]["runtimeConfiguration"]["concurrency"]["repetitions"] == 1
    methods = {a["inputs"]["parameters"]["parameters/method"] for a in actions.values()
               if a.get("type") == "OpenApiConnection"}
    assert methods == {"GET", "POST"}, "never DELETE, MERGE or PUT: existing lists and columns are left alone"
    assert all(a["inputs"]["parameters"]["dataset"] == CONFIG["siteUrl"] for a in actions.values()
               if a.get("type") == "OpenApiConnection")


# ------------------------------------------------------------------------------------ the two flows


@pytest.mark.parametrize("name", ["FleetDecide", "FleetOutboxToLists"])
def test_a_deployed_flow_keeps_the_reviewed_definition_but_for_the_deploy_time_differences(name):
    package = P.deploy_flow(name, CONFIG)
    _check_flowagent_rules(package)
    with open(os.path.join(KC.FLOWS, f"{name}.definition.json"), encoding="utf-8") as f:
        source = P._strip_comments(json.load(f))["properties"]["definition"]
    deployed = package["definition"]
    assert set(deployed["actions"]) == set(source["actions"]) and set(deployed["triggers"]) == set(source["triggers"])
    text = json.dumps(deployed)
    for key in ("siteUrl", "inboxFolderPath") if name == "FleetDecide" else ("siteUrl", "outboxFolderId", "appId", "operator"):
        assert CONFIG[key] in text, f"{name}: {key} was not substituted"


def test_fleet_decide_identifies_the_sender_by_their_own_connection():
    assert P.deploy_flow("FleetDecide", CONFIG)["connectors"] == {
        "shared_office365users": "Invoker", "shared_onedriveforbusiness": "Embedded", "shared_sharepointonline": "Embedded"}


def test_the_outbox_flow_never_writes_sharepoints_own_created_column():
    raw = open(os.path.join(KC.FLOWS, "FleetOutboxToLists.definition.json"), encoding="utf-8").read()
    assert "item/Created" not in raw
    for path in glob.glob(os.path.join(KC.REPO_ROOT, "powerapp", "src", "**", "*.pa.yaml"), recursive=True):
        for line in open(path, encoding="utf-8"):
            if ".Created" in line:
                assert re.search(r"Text\(\w+\.Created\)", line), f"{os.path.basename(path)}: read Created through Text(): {line.strip()}"


def test_the_config_is_refused_until_it_holds_this_tenants_values():
    with pytest.raises(P.Refused, match="example value"):
        P.require(dict(CONFIG, siteUrl="https://contoso.sharepoint.com/sites/FleetAgent"), "lists")
    with pytest.raises(P.Refused, match="not a SharePoint site"):
        P.require(dict(CONFIG, siteUrl="https://tenant.sharepoint.com/sites/Fleet/"), "lists")
    with pytest.raises(P.Refused, match="appId"):
        P.require(dict(CONFIG, appId=""), "flows")
    with pytest.raises(P.Refused, match="appId"):
        P.deploy_flow("FleetOutboxToLists", dict(CONFIG, appId=""))
    P.require(CONFIG, "flows")
    example = json.load(open(os.path.join(BUILD, "fleet.config.example.json"), encoding="utf-8"))
    assert set(CONFIG) <= set(example) and set(example) - set(CONFIG) <= {"_readme", "studioUrl"}


# ------------------------------------------------------------------------------------ the app


def _blank_app(workdir):
    os.makedirs(workdir)
    for name, text in (("App.pa.yaml", "App:\n  Properties:\n    Theme: =PowerAppsTheme\n"),
                       ("Screen1.pa.yaml", "Screens:\n  Screen1:\n    Properties:\n      Fill: =White\n"),
                       ("_EditorState.pa.yaml", "EditorState:\n  ScreensOrder:\n    - Screen1\n")):
        with open(os.path.join(workdir, name), "w", encoding="utf-8") as f:
            f.write(text)


def test_canvas_in_lays_the_app_out_as_the_mcp_server_does_and_canvas_out_restores_it_byte_for_byte(tmp_path, monkeypatch):
    work = str(tmp_path / "FleetAgent")
    _blank_app(work)
    log = P.canvas_in(work)
    assert "removed Screen1.pa.yaml (a screen the app does not have)" in log
    got = sorted(os.path.relpath(p, work).replace(os.sep, "/") for p in glob.glob(os.path.join(work, "**", "*.pa.yaml"), recursive=True))
    screens = [s + ".pa.yaml" for s in P._screens_order()]
    assert got == sorted(["App.pa.yaml", "_EditorState.pa.yaml"] + screens +
                         ["Components/" + os.path.basename(p) for p in glob.glob(os.path.join(P.SRC, "Components", "*.pa.yaml"))])
    mirror = tmp_path / "src"
    shutil.copytree(P.SRC, mirror)
    for path in glob.glob(str(mirror / "**" / "*.pa.yaml"), recursive=True):
        os.remove(path)
    monkeypatch.setattr(P, "SRC", str(mirror))
    P.canvas_out(work)
    for path in glob.glob(os.path.join(KC.REPO_ROOT, "powerapp", "src", "**", "*.pa.yaml"), recursive=True):
        rel = os.path.relpath(path, os.path.join(KC.REPO_ROOT, "powerapp", "src"))
        assert open(path, "rb").read() == (mirror / rel).read_bytes(), rel


def test_canvas_in_refuses_the_repository_root_and_a_directory_with_other_files(tmp_path):
    with pytest.raises(P.Refused, match="repository root"):
        P.canvas_in(KC.REPO_ROOT)
    work = str(tmp_path / "w")
    _blank_app(work)
    open(os.path.join(work, "notes.md"), "w").close()
    with pytest.raises(P.Refused, match=r"\.pa\.yaml files only"):
        P.canvas_in(work)
    with pytest.raises(P.Refused, match="sync_canvas"):
        P.canvas_in(str(tmp_path / "empty"))


# ------------------------------------------------------------------------------------ the instructions


def _instruction_files() -> list[str]:
    return sorted(glob.glob(os.path.join(BUILD, "**", "*.md"), recursive=True)) + [
        os.path.join(KC.REPO_ROOT, ".github", "skills", "build-fleetagent", "SKILL.md"),
        os.path.join(KC.REPO_ROOT, ".github", "copilot-instructions.md")]


def test_every_file_command_and_step_the_instructions_name_exists():
    commands = {"check", "lists", "flows", "canvas-in", "canvas-out"}
    steps = {os.path.basename(p) for p in glob.glob(os.path.join(BUILD, "steps", "*.md"))}
    assert [s[:2] for s in sorted(steps)] == ["01", "02", "03", "04", "05", "06", "07"]
    for path in _instruction_files():
        text = open(path, encoding="utf-8").read()
        for cmd in re.findall(r"build/prepare\.py ([a-z-]+)", text):
            assert cmd in commands, f"{os.path.basename(path)} runs prepare.py {cmd}"
        for step in re.findall(r"build/steps/(\d\d-[a-z-]+\.md)", text):
            assert step in steps, f"{os.path.basename(path)} names {step}"
        for ref in re.findall(r"`((?:powerapp|flows|data|contract|tests|build)/[A-Za-z0-9_./-]+\.(?:md|py|json|yaml|xlsx))`", text):
            if "<" not in ref and not ref.startswith("build/out/") and ref != "build/fleet.config.json":
                assert os.path.exists(os.path.join(KC.REPO_ROOT, ref)), f"{os.path.basename(path)} names {ref}"
    for key, step in {k: n for need in P.NEEDS.values() for k, n in need.items()}.items():
        assert any(s.startswith(step) for s in steps), key


def test_the_column_counts_step_02_checks_are_the_provisioning_flows():
    text = open(os.path.join(BUILD, "steps", "02-lists.md"), encoding="utf-8").read()
    for entry in P.provisioning_spec():
        assert re.search(rf"\| {entry['list']} \| {len(entry['columns'])} \|", text), entry["list"]


def test_the_skill_has_the_frontmatter_copilot_reads():
    text = open(os.path.join(KC.REPO_ROOT, ".github", "skills", "build-fleetagent", "SKILL.md"), encoding="utf-8").read()
    head = text.split("---")[1]
    assert re.search(r"^name: build-fleetagent$", head, re.M) and re.search(r"^description: .{80,}", head, re.M)


def test_the_ignored_files_stay_out_of_git():
    ignore = open(os.path.join(KC.REPO_ROOT, ".gitignore"), encoding="utf-8").read().split("\n")
    assert "build/fleet.config.json" in ignore and "build/out/" in ignore


def test_canvas_out_logs_a_path_on_another_windows_drive_instead_of_failing(tmp_path, monkeypatch):
    """Windows CI: the temp directory is on C: and the checkout on D:, where `os.path.relpath` raises ValueError."""
    real = os.path.relpath

    def across_drives(path, start=os.curdir):
        if os.path.abspath(start) == P.ROOT and not os.path.abspath(path).startswith(P.ROOT):
            raise ValueError("path is on mount 'C:', start on mount 'D:'")
        return real(path, start)

    work = str(tmp_path / "FleetAgent")
    _blank_app(work)
    P.canvas_in(work)
    mirror = tmp_path / "src"
    shutil.copytree(P.SRC, mirror)
    monkeypatch.setattr(P, "SRC", str(mirror))
    monkeypatch.setattr(os.path, "relpath", across_drives)
    log = P.canvas_out(work)
    assert any(line.startswith("App.pa.yaml -> ") and str(mirror) in line for line in log)
