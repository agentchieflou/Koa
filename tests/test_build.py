"""The Copilot build (`build/`): what `build/prepare.py` writes for the operator to import and paste (flow packages,
the list flow's report and its check, the app's pastes, the mirror back from a saved `.msapp`), and the instruction
files that tell an agent when to run it. No MCP server is involved anywhere, and the instructions must never send an
agent to one. An agent follows these files literally, so a step that names a command, a file or a count that does
not exist is a build that stops halfway on the operator's laptop.
"""
from __future__ import annotations
import glob
import importlib.util
import json
import os
import re
import shutil
import zipfile

import pytest

import koa_contract as KC
from test_mobile_powerapp import COLUMNS, LISTS

BUILD = os.path.join(KC.REPO_ROOT, "build")
CONFIG = {"environment": "Default-00000000-0000-0000-0000-000000000000", "siteUrl": "https://tenant.sharepoint.com/sites/Fleet",
          "library": "FleetAgent", "operators": ["op@tenant.example", "two@tenant.example", "three@tenant.example"],
          "appId": "6fc3e3d1-292b-4281-8826-577f78512e56"}


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


def _check_definition_rules(package: dict):
    """What a definition keeps so Power Automate imports it as written: only its own two parameters, no review notes
    or environment variables, no action waiting on one outside its scope, no `authentication` (the import injects
    it), only OpenApiConnection actions, and every connection the package names."""
    definition = package["definition"]
    assert {"$authentication", "$connections"} == set(definition["parameters"]), definition["parameters"].keys()
    text = json.dumps(definition)
    assert "_comment" not in text and "fleet_" not in text
    for name, action, siblings in _actions_with_parents(definition):
        assert set(action.get("runAfter", {})) <= siblings, f"{name} runs after an action outside its scope"
        if action.get("type") == "OpenApiConnection":
            assert "authentication" not in action["inputs"], f"{name}: the import injects authentication"
            assert action["inputs"]["host"]["connectionName"] in package["connectors"], name
        assert action.get("type") != "ApiConnection", name
    assert set(package["connectionRefsTemplate"]) == set(package["connectors"])
    for key, ref in package["connectionRefsTemplate"].items():
        assert ref["source"] == package["connectors"][key] and ref["id"].endswith("/" + key)


# ------------------------------------------------------------------------------------ the lists


def test_the_provisioning_spec_is_the_contracts_columns_less_what_sharepoint_already_has():
    *lists, library = P.provisioning_spec("FleetAgent")
    assert [entry["list"] for entry in lists] == list(LISTS)
    for entry in lists:
        want = [c for c in COLUMNS[entry["list"]] if c not in ("Title", "Created")]
        assert [c["name"] for c in entry["columns"]] == want, entry["list"]
        assert "Operator" in want, "every list is shared by several operators"
        assert entry["indexed"] == ["Title", "Operator"], "every lookup filters on both"
        created = json.loads(entry["create"])
        assert created["Title"] == entry["list"] and created["BaseTemplate"] == 100
    assert library["list"] == "FleetAgent" and library["columns"] == [] and library["indexed"] == []
    assert json.loads(library["create"])["BaseTemplate"] == 101, "the bridge folders live in a document library"


def test_multi_line_columns_are_the_data_readmes_and_every_column_is_plain_text_under_its_own_internal_name():
    spec = {e["list"]: e for e in P.provisioning_spec()[:-1]}
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


def test_the_provisioning_flow_keeps_the_import_rules_and_only_creates_what_is_missing():
    """It creates only what is missing and deletes nothing but permissions: the one DELETE removes a role assignment
    other than the Owners group's, and the one MERGE turns on a column index."""
    package = P.provisioning_flow(CONFIG)
    _check_definition_rules(package)
    assert package["connectors"] == {"shared_sharepointonline": "Embedded"}
    definition = package["definition"]
    assert definition["triggers"]["manual"]["kind"] == "Button"
    actions = {name: action for name, action, _ in _actions_with_parents(definition)}
    for create, guard in (("Create_list", "List_is_missing"), ("Create_column", "Column_is_missing"),
                          ("Create_folder", "Folder_is_missing")):
        [clause] = actions[guard]["expression"]["and"]
        assert create in actions[guard]["actions"] and set(clause["not"]) == {"contains"}
    for name in ("For_each_list", "For_each_column", "For_each_index", "For_each_operator", "For_each_securable",
                 "For_each_assignment"):
        assert actions[name]["runtimeConfiguration"]["concurrency"]["repetitions"] == 1
    requests = [a["inputs"]["parameters"] for a in actions.values() if a.get("type") == "OpenApiConnection"]
    assert {r["parameters/method"] for r in requests} == {"GET", "POST"}
    tunnelled = {r["parameters/headers"].get("X-HTTP-Method"): r["parameters/uri"] for r in requests
                 if r["parameters/headers"].get("X-HTTP-Method")}
    assert set(tunnelled) == {"DELETE", "MERGE"}
    assert "/roleassignments/getbyprincipalid(" in tunnelled["DELETE"], "the only deletion is a permission"
    assert "/fields/getbyinternalnameortitle(" in tunnelled["MERGE"] and "Indexed" in [
        r["parameters/body"] for r in requests if r["parameters/headers"].get("X-HTTP-Method") == "MERGE"][0]
    assert actions["For_each_operator"]["foreach"] == CONFIG["operators"]
    assert all(a["inputs"]["parameters"]["dataset"] == CONFIG["siteUrl"] for a in actions.values()
               if a.get("type") == "OpenApiConnection")


def test_the_lists_and_the_library_are_locked_to_the_sites_owners_and_the_flow_reads_it_back():
    actions = {name: action for name, action, _ in _actions_with_parents(P.provisioning_flow(CONFIG)["definition"])}
    assert actions["For_each_securable"]["foreach"] == "@outputs('Spec')", "all five lists and the library"
    assert actions["Get_owner_group"]["inputs"]["parameters"]["parameters/uri"].startswith("_api/web/associatedownergroup")
    assert "getbytype(5)" in actions["Get_full_control"]["inputs"]["parameters"]["parameters/uri"], "Full Control"
    uri = actions["Break_inheritance"]["inputs"]["parameters"]["parameters/uri"]
    assert "breakroleinheritance(copyRoleAssignments=false" in uri, "nobody's access is copied onto the list"
    assert "addroleassignment(principalid=@{body('Get_owner_group')?['Id']}" in \
        actions["Grant_owners"]["inputs"]["parameters"]["parameters/uri"]
    guard = actions["Not_the_owners"]["expression"]["and"][0]["not"]["equals"]
    assert guard == ["@items('For_each_assignment')?['PrincipalId']", "@body('Get_owner_group')?['Id']"]
    evidence = actions["Owners_only"]["inputs"]["ownersOnly"]
    assert "equals(length(body('Get_assignments_after')?['value']), 1)" in evidence and "Get_owner_group" in evidence
    assert actions["Get_assignments_after"]["runAfter"] == {"For_each_assignment": ["Succeeded"]}


def _report(cfg=CONFIG):
    """The Report a clean run writes: every column SharePoint gives a list plus the contract's, every lock held."""
    lists = [{"list": e["list"], "fields": ["ID", "Title", "Created"] + [c["name"] for c in e["columns"]], "ownersOnly": True}
             for e in P.provisioning_spec(cfg["library"])]
    return {"lists": lists, "folders": ["Forms"] + list(cfg["operators"])}


def test_the_list_flow_ends_in_a_report_that_check_lists_reads():
    definition = P.provisioning_flow(CONFIG)["definition"]
    top = definition["actions"]
    assert top["Initialize_report"]["type"] == "InitializeVariable", "variables are initialised at the top level only"
    last = [n for n, a in top.items() if not any(n in b.get("runAfter", {}) for b in top.values())]
    assert last == ["Report"], "Report runs after everything else"
    assert top["Report"]["inputs"] == {"lists": "@variables('Report')", "folders": "@body('Select_folders_after')"}
    actions = {name: action for name, action, _ in _actions_with_parents(definition)}
    entry = actions["Add_to_report"]["inputs"]["value"]
    assert entry["ownersOnly"] == "@outputs('Owners_only')?['ownersOnly']" and entry["fields"] == "@body('Select_fields_after')"
    assert P.check_lists(_report(), CONFIG) == []
    broken = _report()
    broken["lists"][0]["ownersOnly"] = False
    broken["lists"][1]["fields"] = ["Title"]
    del broken["lists"][2]
    broken["folders"] = broken["folders"][:-1]
    problems = "\n".join(P.check_lists(broken, CONFIG))
    for words in ("FleetAttention: not Owners-only", "FleetApprovals: missing Repo", "FleetDecisions: not in the report",
                  f"FleetAgent: no folder {CONFIG['operators'][-1]}"):
        assert words in problems


def test_the_report_is_read_as_power_automate_shows_it(tmp_path):
    raw = tmp_path / "raw.json"
    raw.write_text(json.dumps({"body": _report()}), encoding="utf-8-sig")
    assert P.read_report(str(raw)) == _report(), "Show raw outputs wraps the value in body"
    plain = tmp_path / "plain.json"
    plain.write_text(json.dumps(_report()), encoding="utf-8")
    assert P.read_report(str(plain)) == _report()
    (tmp_path / "half.json").write_text('{"lists": [', encoding="utf-8")
    with pytest.raises(P.Refused, match="not JSON"):
        P.read_report(str(tmp_path / "half.json"))
    (tmp_path / "other.json").write_text('{"body": {"ok": true}}', encoding="utf-8")
    with pytest.raises(P.Refused, match="no lists"):
        P.read_report(str(tmp_path / "other.json"))
    with pytest.raises(P.Refused, match="does not exist"):
        P.read_report(str(tmp_path / "missing.json"))


@pytest.mark.parametrize("package", [P.provisioning_flow(CONFIG), P.deploy_flow("FleetDecide", CONFIG),
                                     P.deploy_flow("FleetOutboxToLists", CONFIG, CONFIG["operators"][0])],
                         ids=["FleetProvisionLists", "FleetDecide", "FleetOutboxToLists"])
def test_every_flow_is_a_package_laid_out_as_power_automate_exports_one(package, tmp_path):
    """Import Package (Legacy) takes the layout Power Automate exports: a root manifest whose resources are the flow,
    and per connector the API and a connection the importer picks; the flow's folder maps each to its resource."""
    archive, readable = P.write_out(package, str(tmp_path))
    assert archive.endswith(f"{package['name']}.zip") and readable.endswith(f"{package['name']}.json")
    assert json.load(open(readable, encoding="utf-8")) == package
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        files = {n: json.loads(z.read(n)) for n in names}
    manifest = files["manifest.json"]
    [flow] = [rid for rid, r in manifest["resources"].items() if r["type"] == "Microsoft.Flow/flows"]
    assert sorted(names) == sorted(["manifest.json", "Microsoft.Flow/flows/manifest.json"] +
                                   [f"Microsoft.Flow/flows/{flow}/{f}" for f in ("definition.json", "apisMap.json", "connectionsMap.json")])
    assert manifest["schema"] == "1.0" and manifest["details"]["displayName"] == package["name"]
    assert manifest["resources"][flow]["hierarchy"] == "Root" and manifest["resources"][flow]["suggestedCreationType"] == "New"
    assert files["Microsoft.Flow/flows/manifest.json"] == {"packageSchemaVersion": "1.0", "flowAssets": {"assetPaths": [flow]}}
    apis, connections = files[f"Microsoft.Flow/flows/{flow}/apisMap.json"], files[f"Microsoft.Flow/flows/{flow}/connectionsMap.json"]
    assert set(apis) == set(connections) == set(package["connectors"])
    for key in package["connectors"]:
        assert manifest["resources"][apis[key]]["id"] == f"/providers/Microsoft.PowerApps/apis/{key}"
        assert manifest["resources"][connections[key]]["type"] == "Microsoft.PowerApps/apis/connections"
        assert manifest["resources"][connections[key]]["dependsOn"] == [apis[key]]
    assert set(manifest["resources"][flow]["dependsOn"]) == set(apis.values()) | set(connections.values())
    definition = files[f"Microsoft.Flow/flows/{flow}/definition.json"]["properties"]
    assert definition["displayName"] == package["name"] and definition["definition"] == package["definition"]
    assert {k: r["source"] for k, r in definition["connectionReferences"].items()} == package["connectors"]
    again = P.import_package(package, created="2026-01-01T00:00:00.0000000Z")
    assert P.import_package(package, created="2026-01-01T00:00:00.0000000Z") == again, "the same flow, the same ids"


# ------------------------------------------------------------------------------------ the two flows


@pytest.mark.parametrize("name", ["FleetDecide", "FleetOutboxToLists"])
def test_a_deployed_flow_keeps_the_reviewed_definition_but_for_the_deploy_time_differences(name):
    package = P.deploy_flow(name, CONFIG, "" if name == "FleetDecide" else CONFIG["operators"][0])
    _check_definition_rules(package)
    with open(os.path.join(KC.FLOWS, f"{name}.definition.json"), encoding="utf-8") as f:
        source = P._strip_comments(json.load(f))["properties"]["definition"]
    deployed = package["definition"]
    assert set(deployed["actions"]) == set(source["actions"]) and set(deployed["triggers"]) == set(source["triggers"])
    text = json.dumps(deployed)
    for key in ("siteUrl", "library") if name == "FleetDecide" else ("siteUrl", "library", "appId"):
        assert CONFIG[key] in text, f"{name}: {key} was not substituted"
    assert "fleet_" not in text, f"{name}: an environment variable was left in"


def test_fleet_decide_identifies_the_sender_by_their_own_connection():
    assert P.deploy_flow("FleetDecide", CONFIG)["connectors"] == {
        "shared_office365users": "Invoker", "shared_sharepointonline": "Embedded"}
    create = KC.actions(P.deploy_flow("FleetDecide", CONFIG)["definition"])["Create_file"]["inputs"]["parameters"]
    assert create["folderPath"] == "@concat('/', 'FleetAgent', '/', toLower(outputs('Compose_by')), '/inbox')", \
        "the inbox is the sender's own folder, named by the UPN from their own Office 365 connection"


def test_each_operator_gets_a_copy_of_the_outbox_flow_that_reads_only_their_folder():
    """One copy per operator: a single flow for three laptops would pass the 10,000 requests a cloud flow may make
    in a day on an Office 365 licence (flows/README.md, Request budget)."""
    packages = [P.deploy_flow("FleetOutboxToLists", CONFIG, op) for op in CONFIG["operators"]]
    assert [p["name"] for p in packages] == [f"FleetOutboxToLists ({op})" for op in CONFIG["operators"]]
    for op, package in zip(CONFIG["operators"], packages):
        [trigger] = package["definition"]["triggers"].values()
        assert trigger["inputs"]["host"]["operationId"] == "GetOnNewFileItems"
        assert trigger["inputs"]["parameters"]["table"] == CONFIG["library"]
        assert trigger["inputs"]["parameters"]["folderPath"] == f"/{CONFIG['library']}/{op}"
        [condition] = trigger["conditions"]
        assert f"'/', '{op}', '/outbox/'" in condition["expression"], \
            "a file outside this operator's outbox never starts this copy, whatever the trigger's folder does"
        assert KC.actions(package["definition"])["Compose_operator"]["inputs"] == op
    with pytest.raises(P.Refused, match="operators"):
        P.deploy_flow("FleetOutboxToLists", CONFIG)


def test_the_outbox_flow_keys_every_row_and_push_by_its_operator():
    definition = P.deploy_flow("FleetOutboxToLists", CONFIG, CONFIG["operators"][0])["definition"]
    acts = KC.actions(definition)
    for name, action in acts.items():
        if action.get("type") != "OpenApiConnection":
            continue
        params, op = action["inputs"]["parameters"], action["inputs"]["host"]["operationId"]
        if op == "GetItems":
            assert "Compose_operator" in params["$filter"], name
        if op in ("PostItem", "PatchItem"):
            key = "item/Title" if params["table"] == "FleetHeartbeat" else "item/Operator"
            assert "Compose_operator" in params[key], name
        if op == "SendPushNotificationV2":
            assert params["recipients"] == ["@outputs('Compose_operator')"], name


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
    with pytest.raises(P.Refused, match="lowercase UPN"):
        P.require(dict(CONFIG, operators=["Op@Tenant.example"]), "lists")
    with pytest.raises(P.Refused, match="lowercase UPN"):
        P.require(dict(CONFIG, operators=["op#1@tenant.example"]), "lists")
    with pytest.raises(P.Refused, match="twice"):
        P.require(dict(CONFIG, operators=["op@tenant.example", "op@tenant.example"]), "lists")
    with pytest.raises(P.Refused, match="operators"):
        P.require(dict(CONFIG, operators=[]), "lists")
    with pytest.raises(P.Refused, match="example values"):
        P.require(dict(CONFIG, operators=["you@contoso.com"]), "lists")
    with pytest.raises(P.Refused, match="appId"):
        P.deploy_flow("FleetOutboxToLists", dict(CONFIG, appId=""), CONFIG["operators"][0])
    P.require(CONFIG, "flows")
    example = json.load(open(os.path.join(BUILD, "fleet.config.example.json"), encoding="utf-8"))
    assert set(CONFIG) <= set(example) and set(example) - set(CONFIG) <= {"_readme", "studioUrl"}


# ------------------------------------------------------------------------------------ the app


def test_the_pastes_are_every_component_then_every_screen_then_the_app_object():
    plan = P.paste_plan()
    assert [i["n"] for i in plan] == list(range(1, len(plan) + 1))
    names = [i["name"] for i in plan]
    components = sorted(os.path.basename(p)[:-len(".pa.yaml")] for p in glob.glob(os.path.join(P.SRC, "Components", "*.pa.yaml")))
    screens = sorted(os.path.basename(p)[:-len(".pa.yaml")] for p in glob.glob(os.path.join(P.SRC, "Screens", "*.pa.yaml")))
    assert sorted(names[:len(components)]) == components, "components first: the screens use them"
    assert sorted(names[len(components):len(components) + len(screens)]) == screens
    assert names[-4:] == ["App.Formulas", "App.OnError", "App.BackEnabled", "App.StartScreen"]
    assert names.index("HomeScreen") == len(components) + len(screens) - 1, "HomeScreen last: every back button names it"
    readme = open(os.path.join(KC.REPO_ROOT, "README.md"), encoding="utf-8").read()
    assert "`SettingsScreen`, `ReplyScreen`, `DecideScreen`,\n      `ApprovalScreen`, `AgentScreen`, `HomeScreen`" in readme, \
        "the by-hand sheet pastes in the same order"
    assert re.search(rf"in the order that leaves the fewest names unresolved", open(os.path.join(BUILD, "steps", "06-app.md"), encoding="utf-8").read())
    assert f"thirteen pastes" in open(os.path.join(BUILD, "steps", "06-app.md"), encoding="utf-8").read() and len(plan) == 13


def test_the_app_object_goes_into_the_formula_bar_without_its_equals_sign():
    props = P.app_properties()
    assert list(props) == list(P.APP_PROPERTIES)
    assert props["BackEnabled"] == "true" and props["StartScreen"].startswith("If(Param(")
    assert props["Formulas"].startswith("// Named formulas only.") and "\nMe = Lower(User().Email);" in props["Formulas"]
    assert props["OnError"].startswith("Trace(") and props["OnError"].endswith("Error(FirstError)")
    assert not any(v.startswith("=") for v in props.values())


def test_paste_writes_each_paste_and_puts_the_one_asked_for_on_the_clipboard(tmp_path, monkeypatch, capsys):
    plan = P.write_paste(str(tmp_path))
    for item in plan:
        written = open(item["path"], "rb").read()
        if "source" in item:
            assert written == open(item["source"], "rb").read(), item["name"]
        else:
            assert written.decode("utf-8") == item["text"] + "\n"
    monkeypatch.setattr(P, "OUT", str(tmp_path))
    copied = []
    monkeypatch.setattr(P, "to_clipboard", lambda path: copied.append(path) or True)
    assert P.main(["paste", "4"]) == 0
    assert copied and copied[0].endswith(plan[3]["file"]) and "on the clipboard" in capsys.readouterr().out
    monkeypatch.setattr(P, "to_clipboard", lambda path: False)
    assert P.main(["paste", "1"]) == 0 and "open it, copy all" in capsys.readouterr().out
    assert P.main(["paste", str(len(plan) + 1)]) == 2


def _msapp(path, src_prefix="Src", component_dir="Components"):
    """A saved .msapp as Studio writes it: its own files, and the source under Src/."""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("Header.json", "{}")
        z.writestr("Controls/1.json", "{}")
        for source in glob.glob(os.path.join(P.SRC, "**", "*.pa.yaml"), recursive=True):
            rel = os.path.relpath(source, P.SRC).replace(os.sep, "/")
            if rel.startswith("Screens/"):
                rel = rel.split("/", 1)[1]
            elif rel.startswith("Components/"):
                rel = f"{component_dir}/" + rel.split("/", 1)[1]
            z.writestr(f"{src_prefix}/{rel}", open(source, "rb").read().replace(b"\n", b"\r\n"))


@pytest.mark.parametrize("component_dir", ["Components", "Component"])
def test_canvas_out_restores_the_app_byte_for_byte_from_a_saved_msapp(component_dir, tmp_path, monkeypatch):
    saved = str(tmp_path / "FleetAgent.msapp")
    _msapp(saved, component_dir=component_dir)
    mirror = tmp_path / "src"
    shutil.copytree(P.SRC, mirror)
    for path in glob.glob(str(mirror / "**" / "*.pa.yaml"), recursive=True):
        os.remove(path)
    monkeypatch.setattr(P, "SRC", str(mirror))
    log = P.canvas_out(saved)
    assert any(line.startswith("App.pa.yaml -> ") for line in log)
    for path in glob.glob(os.path.join(KC.REPO_ROOT, "powerapp", "src", "**", "*.pa.yaml"), recursive=True):
        rel = os.path.relpath(path, os.path.join(KC.REPO_ROOT, "powerapp", "src"))
        assert open(path, "rb").read() == (mirror / rel).read_bytes(), rel


def test_canvas_out_refuses_a_file_that_is_not_a_saved_app(tmp_path):
    empty = str(tmp_path / "empty.msapp")
    with zipfile.ZipFile(empty, "w") as z:
        z.writestr("Header.json", "{}")
    with pytest.raises(P.Refused, match="Src/App.pa.yaml"):
        P.canvas_out(empty)
    os.makedirs(tmp_path / "nothing")
    with pytest.raises(P.Refused, match="no App.pa.yaml"):
        P.canvas_out(str(tmp_path / "nothing"))


# ------------------------------------------------------------------------------------ the instructions


def _instruction_files() -> list[str]:
    return sorted(glob.glob(os.path.join(BUILD, "**", "*.md"), recursive=True)) + [
        os.path.join(KC.REPO_ROOT, ".github", "skills", "build-fleetagent", "SKILL.md"),
        os.path.join(KC.REPO_ROOT, ".github", "copilot-instructions.md")]


def test_every_file_command_and_step_the_instructions_name_exists():
    commands = {"check", "lists", "check-lists", "flows", "paste", "canvas-out"}
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
    for entry in P.provisioning_spec()[:-1]:                # the five lists; the library has no columns
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

    saved = str(tmp_path / "FleetAgent.msapp")
    _msapp(saved)
    mirror = tmp_path / "src"
    shutil.copytree(P.SRC, mirror)
    monkeypatch.setattr(P, "SRC", str(mirror))
    monkeypatch.setattr(os.path, "relpath", across_drives)
    log = P.canvas_out(saved)
    assert any(line.startswith("App.pa.yaml -> ") and str(mirror) in line for line in log)


#: What an instruction would say to send an agent to an MCP server or a plugin that brings one.
MCP_TOOLS = ("sync_canvas", "compile_canvas", "describe_control", "list_data_sources", "get_data_source_schema",
             "list_apis", "describe_api", "list_controls", "create_flow", "update_flow", "publish_flow", "run_flow",
             "delete_flow", "list_flows", "get_flow", "preflight_flow", "validate_flow", "pick_or_create_connection",
             "list_environments", "set_current_env", "get_run_history", "get_run_details", "get_run_actions",
             "get_run_action_repetitions", "diagnose_run", "get_operation_details", "microsoft_docs_search",
             "microsoft_docs_fetch", "microsoft_code_sample_search")
MCP_SETUP = ("/plugin install", "/plugin marketplace", "@agentPlugins", "chat.plugins.enabled", "configure-canvas-mcp",
             "mcp.json", "flowagent-", "canvas-authoring-", "mcp__")


def test_no_instruction_sends_an_agent_to_an_mcp_server():
    """The organisation blocks MCP servers: no instruction may name an MCP tool or the setup of one, and the rules an
    agent reads first say so."""
    files = _instruction_files() + sorted(glob.glob(os.path.join(KC.REPO_ROOT, ".github", "skills", "*", "SKILL.md"))) + \
        sorted(glob.glob(os.path.join(KC.REPO_ROOT, ".github", "prompts", "*.md"))) + [
            os.path.join(KC.REPO_ROOT, name) for name in ("AGENTS.md", "README.md", "site/README.md", "site/intake/README.md",
                                                          "powerapp/NOTES.md", "flows/README.md", "data/README.md")]
    for path in sorted(set(files)):
        text = open(path, encoding="utf-8").read()
        for word in MCP_TOOLS + MCP_SETUP:
            assert word not in text, f"{os.path.relpath(path, KC.REPO_ROOT)} names {word}"
    rules = open(os.path.join(KC.REPO_ROOT, ".github", "copilot-instructions.md"), encoding="utf-8").read()
    assert "**No MCP servers.**" in rules and "Never call an MCP tool" in rules
    assert "**No MCP servers.**" in open(os.path.join(KC.REPO_ROOT, "AGENTS.md"), encoding="utf-8").read()
    for skill in glob.glob(os.path.join(KC.REPO_ROOT, ".github", "skills", "build-*", "SKILL.md")):
        assert "You have no MCP tools" in open(skill, encoding="utf-8").read(), skill
