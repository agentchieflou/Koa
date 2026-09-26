"""The FleetAgent canvas app is authored as Power Apps YAML (schema v3.0) under `mobile/powerapp/src`,
and nothing in this repository can compile it: Studio does that when the operator pastes the screens.
What CI can do, with pyyaml alone, is hold the sources to the shape the schema demands and to the
app's own ground rules, so that a paste fails in Studio only for reasons this file could not see.

Two families of guard. The schema family (root keys, one-key children, control-type pattern, `=`
formulas, component property kinds, editor state) re-implements the handful of schema rules that
matter for a hand-authored tree; the full Draft 7 validation is run locally as `mobile/README.md`
says, because `jsonschema` is a dev extra and the official schema's PCF pattern does not even compile
under Python's `re`. The ground-rule family (five lists and one flow, touch sizes, accessible labels,
one timer, no overlays, no tenant ids, colour by a closed set) is the contract the laptop bridge and
the flows build to, so a drift here is a drift the phone would show as a wrong screen.
"""
from __future__ import annotations
import glob
import json
import os
import re

import pytest
import yaml

from agentdata.fleet.agentstate import STATES, STATE_ROLES, needs_the_human
from agentdata.fleet.notify import SEVERITIES

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOBILE = os.path.join(REPO_ROOT, "mobile", "powerapp")
SRC = os.path.join(MOBILE, "src")
SCHEMA = os.path.join(MOBILE, "schema", "pa.schema.yaml")
SAMPLE = os.path.join(MOBILE, "sample")
THEME = os.path.join(MOBILE, "themes", "FleetTheme.yaml")

ROOT_KEYS = ("App", "Screens", "ComponentDefinitions", "DataSources", "EditorState")
#: The five lists and the one flow the app may name. Anything else is a data source Studio has not
#: been told about, which pastes as "name isn't recognized" on every formula that uses it.
LISTS = ("FleetAttention", "FleetApprovals", "FleetDecisions", "FleetNotifications", "FleetHeartbeat")
FLOW = "FleetDecide"
#: Control names carry a type prefix so a formula reads without the tree view (`cmp` is a component
#: instance; the rest are the control families the app uses).
NAME = re.compile(r"^(con|lbl|btn|gal|txt|bdg|ico|tab|tmr|spn|cmp)[A-Z][A-Za-z0-9]*$")
NUMBER = re.compile(r"^=\s*-?\d+(\.\d+)?\s*$")
#: Power Fx text literals, `""` being the escape for a quote inside one.
STRING = re.compile(r'"(?:[^"]|"")*"')
#: Modern controls have no TabIndex (Learn: `AcceptsFocus` was removed, "always accepts keyboard
#: focus"); the classic ones the app uses still carry it.
CLASSIC_WITH_TAB_INDEX = ("Gallery", "Timer")

#: The contract every list column keeps: text, one line unless the bridge says multi-line.
COLUMNS = {
    "FleetAttention": ["Title", "Project", "Ticket", "State", "Role", "NeedsHuman", "Says", "LastSaid",
                       "AgeSeconds", "At", "Generated", "ApprovalId", "ApprovalsJson", "QuestionsJson",
                       "RunNumber", "RunOrigin", "RunLive", "Model", "SpendLine", "SpendTotal", "SpendToday",
                       "SpendBudget", "Turns", "Supervised", "External", "Digest", "Seq"],
    "FleetApprovals": ["Title", "Repo", "Ticket", "ApprovalKind", "Summary", "PayloadPreview", "PayloadTruncated",
                       "PayloadBytes", "Digest", "Created", "Expires", "WaitingSeconds", "Status", "DecidedBy",
                       "DecidedAt", "Reason", "Via", "Late", "Nonce", "ResultCode", "ResultText", "SourceFile"],
    "FleetDecisions": ["Title", "Kind", "ApprovalId", "Repo", "Decision", "Reason", "Message", "AnswersJson",
                       "Digest", "By", "Device", "Issued", "Expires", "InboxFile", "Result", "ResultCode",
                       "ResultText", "ResultAt"],
    "FleetNotifications": ["Title", "Repo", "Ticket", "State", "Severity", "TitleText", "Body", "At", "Seq",
                           "Quiet", "ApprovalId", "SourceFile"],
    "FleetHeartbeat": ["Title", "At", "EverySeconds", "ExpireSeconds", "Contract", "Operator", "Bridge", "LaptopId",
                       "ServeUp", "DeskStreams", "Repos", "NeedsHuman", "ApprovalsPending", "Notifications24h",
                       "Rejected24h", "InboxLastSeen"],
}
CLOSED_SETS = {
    ("FleetAttention", "State"): set(STATES),
    ("FleetAttention", "Role"): set(STATE_ROLES.values()),
    ("FleetApprovals", "Status"): {"pending", "sent", "approved", "denied", "rejected", "expired"},
    ("FleetApprovals", "Via"): {"", "laptop", "mobile"},
    ("FleetDecisions", "Kind"): {"decision", "reply"},
    ("FleetDecisions", "Result"): {"sent", "applied", "rejected"},
    ("FleetNotifications", "Severity"): set(SEVERITIES),
}
STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
STAMP_COLUMNS = ("At", "Generated", "Created", "Expires", "DecidedAt", "Issued", "ResultAt", "InboxLastSeen")
#: The text booleans, per table: the heartbeat's NeedsHuman is a count, not a flag.
BOOLEANS = {("FleetAttention", "NeedsHuman"), ("FleetAttention", "RunLive"), ("FleetAttention", "Supervised"),
            ("FleetAttention", "External"), ("FleetApprovals", "PayloadTruncated"), ("FleetApprovals", "Late"),
            ("FleetNotifications", "Quiet"), ("FleetHeartbeat", "ServeUp")}
#: What a sample row must never carry: a UNC or drive path, a URL, a credential shape, a hostname.
LEAK = re.compile(r"\\\\|[A-Za-z]:[\\/]|https?://|gh[pousr]_[A-Za-z0-9]{16,}|xox[baprs]-|eyJ[A-Za-z0-9_-]{10,}"
                  r"|\.corp\.|\.local\b|sharepoint\.com|onmicrosoft\.com")


# ------------------------------------------------------------------------------------ helpers


def _files() -> list[str]:
    return sorted(glob.glob(os.path.join(SRC, "**", "*.pa.yaml"), recursive=True))


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _sources() -> dict[str, dict]:
    files = _files()
    assert files, f"no .pa.yaml under {SRC}"
    return {path: _load(path) for path in files}


def _screens() -> dict[str, dict]:
    out = {}
    for doc in _sources().values():
        out.update(doc.get("Screens") or {})
    return out


def _components() -> dict[str, dict]:
    out = {}
    for doc in _sources().values():
        out.update(doc.get("ComponentDefinitions") or {})
    return out


def _controls(children, parent=None, inside_gallery=False):
    """Every control in a `Children` sequence, depth first: (name, control, parent control or None,
    whether a gallery template encloses it)."""
    for item in children or []:
        (name, control), = item.items()
        yield name, control, parent, inside_gallery
        nested = inside_gallery or control.get("Control") == "Gallery"
        yield from _controls(control.get("Children"), control, nested)


def _all_controls():
    """(owner, name, control, parent, inside_gallery) across every screen and component."""
    for screen, body in _screens().items():
        for name, control, parent, nested in _controls(body.get("Children")):
            yield screen, name, control, parent, nested
    for component, body in _components().items():
        for name, control, parent, nested in _controls(body.get("Children")):
            yield component, name, control, parent, nested


def _formulas():
    """(owner, holder, property, formula) for every formula in the app: the App object, screen
    properties, control properties, component properties and custom-property defaults."""
    for path, doc in _sources().items():
        app = doc.get("App") or {}
        for prop, formula in (app.get("Properties") or {}).items():
            yield "App", "App", prop, formula
        for screen, body in (doc.get("Screens") or {}).items():
            for prop, formula in (body.get("Properties") or {}).items():
                yield screen, screen, prop, formula
            for name, control, _, _ in _controls(body.get("Children")):
                for prop, formula in (control.get("Properties") or {}).items():
                    yield screen, name, prop, formula
        for component, body in (doc.get("ComponentDefinitions") or {}).items():
            for prop, formula in (body.get("Properties") or {}).items():
                yield component, component, prop, formula
            for prop, custom in (body.get("CustomProperties") or {}).items():
                if "Default" in custom:
                    yield component, component, f"{prop}.Default", custom["Default"]
            for name, control, _, _ in _controls(body.get("Children")):
                for prop, formula in (control.get("Properties") or {}).items():
                    yield component, name, prop, formula


def _code(formula: str) -> str:
    """The formula with its text literals blanked, so a word inside quotes is not a reference."""
    return STRING.sub('""', formula or "")


def _type(control: dict) -> str:
    return (control.get("Control") or "").split("@", 1)[0]


def _number(formula) -> float | None:
    return float(formula[1:]) if isinstance(formula, str) and NUMBER.match(formula) else None


# ------------------------------------------------------------------------------- the schema shape


def test_the_sources_hold_one_entity_per_file_in_studios_layout():
    """`App.pa.yaml`, `_EditorState.pa.yaml`, `Screens/<Name>.pa.yaml`, `Components/<Name>.pa.yaml`:
    the layout Studio and the Git integration write, so a file maps to one paste."""
    for path, doc in _sources().items():
        rel = os.path.relpath(path, SRC).replace(os.sep, "/")
        assert isinstance(doc, dict) and len(doc) == 1, f"{rel} must hold exactly one top-level entity"
        (key, body), = doc.items()
        if rel == "App.pa.yaml":
            assert key == "App"
        elif rel == "_EditorState.pa.yaml":
            assert key == "EditorState"
        elif rel.startswith("Screens/"):
            assert key == "Screens" and list(body) == [rel[len("Screens/"):-len(".pa.yaml")]], rel
        elif rel.startswith("Components/"):
            assert key == "ComponentDefinitions" and list(body) == [rel[len("Components/"):-len(".pa.yaml")]], rel
        else:
            pytest.fail(f"{rel} is outside Studio's source layout")
    names = [os.path.basename(p) for p in _files()]
    assert "App.pa.yaml" in names and "_EditorState.pa.yaml" in names


def test_only_the_five_root_keys_are_used():
    for path, doc in _sources().items():
        extra = set(doc) - set(ROOT_KEYS)
        assert not extra, f"{os.path.basename(path)} has root keys the schema forbids: {sorted(extra)}"
    assert not any("DataSources" in doc for doc in _sources().values()), (
        "SharePoint and Excel data sources cannot be expressed in the v3.0 schema; they are added in Studio")


def test_every_child_is_a_single_key_mapping():
    def check(children, where):
        for item in children or []:
            assert isinstance(item, dict) and len(item) == 1, f"{where}: a Children item is not a one-key mapping: {item!r:.80}"
            (name, control), = item.items()
            assert isinstance(control, dict) and "Control" in control, f"{where}/{name} has no Control"
            check(control.get("Children"), f"{where}/{name}")

    for screen, body in _screens().items():
        check(body.get("Children"), screen)
    for component, body in _components().items():
        check(body.get("Children"), component)


def test_every_control_type_matches_the_schema_pattern_and_is_allowed():
    schema = _load(SCHEMA)["definitions"]
    pattern = re.compile(schema["ControlTypeId-pattern"]["pattern"].strip())
    disallowed = set(schema["ControlTypeId-disallowed-types"]["enum"]) | set(schema["ControlTypeId-not-yet-supported"]["enum"])
    for owner, name, control, _, _ in _all_controls():
        value = control["Control"]
        assert pattern.match(value), f"{owner}/{name}: Control {value!r} does not match the schema pattern"
        assert value.split("@")[0] not in disallowed, f"{owner}/{name}: Control {value!r} is disallowed"
        assert "@" not in value, f"{owner}/{name}: {value!r} carries a version; the sources omit versions on purpose"
        keys = set(control) - {"Control", "Properties", "Children", "Variant", "Group", "ComponentName", "Layout",
                               "MetadataKey", "IsLocked", "ComponentLibraryUniqueName"}
        assert not keys, f"{owner}/{name}: unknown instance keys {sorted(keys)}"


def test_every_property_value_is_a_formula_starting_with_equals():
    for owner, holder, prop, formula in _formulas():
        assert formula is None or (isinstance(formula, str) and formula.startswith("=")), (
            f"{owner}/{holder}.{prop} is not a Power Fx formula: {formula!r:.80}")


def test_no_source_file_contains_a_tab_or_a_carriage_return():
    for path in _files() + [THEME]:
        raw = open(path, "rb").read()
        assert b"\t" not in raw, f"{os.path.basename(path)} contains a tab (Studio: 'cannot start any token')"
        assert b"\r" not in raw, f"{os.path.basename(path)} is not LF"


def test_a_single_line_formula_never_holds_a_colon_space_or_a_hash():
    """The YAML grammar: `: ` and ` #` end a plain scalar, so a formula containing either is single-
    quoted or a `|-` block. Checked on the raw lines, because once loaded the quoting is gone."""
    plain = re.compile(r"^\s*[A-Za-z_]\w*:\s+(=.*)$")
    for path in _files():
        for n, line in enumerate(open(path, encoding="utf-8"), 1):
            m = plain.match(line.rstrip("\n"))
            if not m:
                continue
            assert ": " not in m.group(1), f"{os.path.basename(path)}:{n}: ': ' in a plain formula; quote it or use |-"
            assert " #" not in m.group(1), f"{os.path.basename(path)}:{n}: ' #' in a plain formula"
    # and therefore every loaded formula that does contain ': ' came from a quoted or block scalar
    assert any(": " in (f or "") for _, _, _, f in _formulas()), "the check above has nothing to bite on"


def test_component_definitions_are_canvas_components_with_typed_custom_properties():
    kinds_with_data_type = {"Input", "Output"}
    kinds_with_return_type = {"InputFunction", "OutputFunction", "Event", "Action"}
    for name, body in _components().items():
        assert body.get("DefinitionType") == "CanvasComponent", name
        assert body.get("AccessAppScope") is False, f"{name}: components must not read app scope"
        assert body.get("Description"), f"{name} has no Description"
        for prop, custom in (body.get("CustomProperties") or {}).items():
            kind = custom.get("PropertyKind")
            assert kind in kinds_with_data_type | kinds_with_return_type, f"{name}.{prop}: PropertyKind {kind!r}"
            if kind in kinds_with_data_type:
                assert "DataType" in custom and "ReturnType" not in custom, f"{name}.{prop} ({kind}) needs DataType"
            else:
                assert "ReturnType" in custom and "DataType" not in custom, f"{name}.{prop} ({kind}) needs ReturnType"
            if kind == "Input":
                assert "Default" in custom, f"{name}.{prop}: an Input without a Default fails an instance that omits it"


def test_component_definition_properties_never_carry_x_y_or_visible():
    for name, body in _components().items():
        props = set(body.get("Properties") or {})
        assert not props & {"X", "Y", "Visible"}, f"{name}: X, Y and Visible belong to the instance"
        assert {"Width", "Height"} <= props, f"{name}: a definition sets its own Width and Height"


def test_every_component_instance_names_a_component_that_exists_and_sets_its_inputs():
    components = _components()
    for owner, name, control, _, _ in _all_controls():
        if control["Control"] != "CanvasComponent":
            assert "ComponentName" not in control, f"{owner}/{name}"
            continue
        target = control.get("ComponentName")
        assert target in components, f"{owner}/{name} instantiates {target!r}, which is not defined"
        assert set(control) <= {"Control", "ComponentName", "Properties", "Group"}, f"{owner}/{name}: {sorted(control)}"
        custom = components[target].get("CustomProperties") or {}
        set_here = set(control.get("Properties") or {})
        events = {p for p, c in custom.items() if c["PropertyKind"] == "Event"}
        assert events <= set_here, f"{owner}/{name}: events not handled: {sorted(events - set_here)}"


def test_the_editor_state_lists_exactly_the_screens_and_components():
    state = _load(os.path.join(SRC, "_EditorState.pa.yaml"))["EditorState"]
    assert sorted(state["ScreensOrder"]) == sorted(_screens()), "ScreensOrder drifted from Screens/"
    assert sorted(state["ComponentDefinitionsOrder"]) == sorted(_components()), "ComponentDefinitionsOrder drifted"
    assert state["ScreensOrder"][0] == "HomeScreen"
    assert len(set(state["ScreensOrder"])) == len(state["ScreensOrder"])


# ------------------------------------------------------------------------------- the ground rules


def test_formulas_reference_only_the_five_lists_and_the_flow():
    allowed = set(LISTS) | {FLOW} | set(_components())
    for owner, holder, prop, formula in _formulas():
        for token in re.findall(r"\bFleet[A-Za-z0-9]+", _code(formula)):
            assert token in allowed, f"{owner}/{holder}.{prop} names {token!r}, which is not a list, the flow or a component"
    used = {t for _, _, _, f in _formulas() for t in re.findall(r"\bFleet[A-Za-z0-9]+", _code(f))}
    assert set(LISTS) | {FLOW} <= used, f"a list or the flow is never used: {sorted((set(LISTS) | {FLOW}) - used)}"


def test_components_read_only_their_own_properties():
    """AccessAppScope is false: a component may not name a list, the flow, a global or a screen."""
    for component, body in _components().items():
        for name, control, _, _ in _controls(body.get("Children")):
            for prop, formula in (control.get("Properties") or {}).items():
                code = _code(formula)
                assert "UpdateContext(" not in code, f"{component}/{name}.{prop} uses UpdateContext inside a component"
                for token in re.findall(r"\bFleet[A-Za-z0-9]+", code):
                    assert token == component, f"{component}/{name}.{prop} reaches outside the component: {token}"
                assert not re.search(r"\b(sel[A-Z]\w*|busy|decideChoice|App\.)", code), (
                    f"{component}/{name}.{prop} names app state: {formula!r:.80}")


def test_the_flow_is_called_only_inside_if_error_and_its_error_is_shown():
    calls = [(o, h, p, f) for o, h, p, f in _formulas() if f"{FLOW}.Run(" in _code(f)]
    assert sorted((o, h) for o, h, _, _ in calls) == [("DecideScreen", "btnDecideSend"), ("ReplyScreen", "btnReplySend")]
    for owner, holder, prop, formula in calls:
        code = _code(formula)
        assert prop == "OnSelect"
        assert "IfError(" in code and "FirstError.Message" in code, f"{owner}/{holder}: the flow call is not wrapped"
        assert "r.error" in code and "NotificationType.Error" in code, f"{owner}/{holder}: the flow's error is not shown"
        assert "r.ok" in code and "NotificationType.Success" in code
        assert code.startswith("=Set(busy, true)") and code.rstrip().endswith("Set(busy, false)"), f"{owner}/{holder}"
        assert "ExpireSeconds" in code and "Host.OSType" in code
    decide = next(f for o, h, _, f in calls if h == "btnDecideSend")
    assert re.search(rf'{FLOW}\.Run\("decision", selApproval\.Title, selApproval\.Repo, decideChoice, Trim\(txtReason\.Text\), "", "", selApproval\.Digest', decide)
    reply = next(f for o, h, _, f in calls if h == "btnReplySend")
    assert re.search(rf'{FLOW}\.Run\("reply", "", selAttention\.Title, "", "", Trim\(txtMessage\.Text\), "", ""', reply)


def test_buttons_and_inputs_are_at_least_44_high_and_icon_buttons_as_wide():
    for owner, name, control, _, _ in _all_controls():
        kind = _type(control)
        if kind not in ("ModernButton", "ModernTextInput"):
            continue
        props = control.get("Properties") or {}
        height = _number(props.get("Height"))
        assert height is not None and height >= 44, f"{owner}/{name}: Height {props.get('Height')!r} is under 44"
        if kind == "ModernButton" and "IconOnly" in (props.get("Layout") or ""):
            width = _number(props.get("Width"))
            assert width is not None and width >= 44, f"{owner}/{name}: an icon-only button needs Width >= 44"
        if kind == "ModernTextInput":
            assert "Multiline" in props.get("Type", ""), f"{owner}/{name}: the app's inputs are multi-line"
            assert _number(props.get("MaxLength")) is not None, f"{owner}/{name}: set MaxLength"
            assert height >= 96, f"{owner}/{name}: a multi-line input is at least 96 high"


def test_every_interactive_control_has_an_accessible_label():
    for owner, name, control, _, _ in _all_controls():
        kind = _type(control)
        props = control.get("Properties") or {}
        interactive = kind in ("ModernButton", "ModernTextInput", "ModernTabList", "Gallery") or (
            kind == "ModernIcon" and "OnSelect" in props)
        if not interactive:
            continue
        assert props.get("AccessibleLabel", "").startswith("="), f"{owner}/{name} ({kind}) has no AccessibleLabel"
        if kind == "Gallery":
            assert props.get("ItemAccessibleLabel", "").startswith("="), f"{owner}/{name}: a gallery row needs ItemAccessibleLabel"
            assert props.get("Selectable") in ("=true", "=false"), f"{owner}/{name}: say whether rows are selectable"


def test_classic_controls_carry_a_tab_index_of_zero_or_minus_one_and_modern_ones_none():
    for owner, name, control, _, _ in _all_controls():
        props = control.get("Properties") or {}
        if _type(control) in CLASSIC_WITH_TAB_INDEX:
            assert props.get("TabIndex") in ("=0", "=-1"), f"{owner}/{name}: TabIndex must be 0 or -1"
        elif _type(control).startswith("Modern"):
            assert "TabIndex" not in props, f"{owner}/{name}: modern controls have no TabIndex (Learn: AcceptsFocus removed)"


def test_control_names_carry_a_type_prefix_and_are_unique_across_the_app():
    """A control is referenced by name from anywhere in a canvas app, so a name is unique across
    every screen and component, not only inside the one that declares it."""
    seen: dict[str, str] = {}
    for owner, name, control, _, _ in _all_controls():
        assert NAME.match(name), f"{owner}/{name}: control names are <prefix><PascalCase>"
        prefix = NAME.match(name).group(1)
        kind = _type(control)
        expected = {"GroupContainer": "con", "ModernText": "lbl", "ModernButton": "btn", "Gallery": "gal",
                    "ModernTextInput": "txt", "Badge": "bdg", "ModernIcon": "ico", "ModernTabList": "tab",
                    "Timer": "tmr", "ModernSpinner": "spn", "CanvasComponent": "cmp"}[kind]
        assert prefix == expected, f"{owner}/{name}: a {kind} is prefixed {expected}"
        assert name not in seen, f"{name} is declared in both {seen.get(name)} and {owner}"
        seen[name] = owner
    assert not set(seen) & (set(_screens()) | set(_components())), "a control shares a name with a screen or a component"
    for screen in _screens():
        assert screen.endswith("Screen"), f"{screen}: screen names end in Screen (the screen reader announces them)"


def test_the_only_timer_is_the_refresh_timer_on_the_home_screen():
    timers = [(o, n, c) for o, n, c, _, _ in _all_controls() if _type(c) == "Timer"]
    assert [(o, n) for o, n, _ in timers] == [("HomeScreen", "tmrRefresh")]
    props = timers[0][2]["Properties"]
    assert props["Visible"] == "=false" and props["Repeat"] == "=true" and props["AutoStart"] == "=true"
    assert _number(props["Duration"]) == 60000
    for source in LISTS:
        assert f"Refresh({source})" in props["OnTimerEnd"], f"the timer does not refresh {source}"


def test_no_control_is_positioned_absolutely_so_nothing_can_be_an_overlay():
    """Dialogs on top of content are not accessible in canvas apps (Learn); every 'dialog' here is a
    screen, and the way that stays true is that no control on a screen has an X or a Y."""
    for owner, name, control, _, _ in _all_controls():
        props = control.get("Properties") or {}
        assert "X" not in props and "Y" not in props, f"{owner}/{name} is positioned absolutely"
    for name, body in _components().items():
        for _, control, _, _ in _controls(body.get("Children")):
            assert "X" not in (control.get("Properties") or {}), name


def test_no_tenant_ids_site_urls_emails_or_app_ids_are_hard_coded():
    guid = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
    email = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
    for path in _files():
        text = open(path, encoding="utf-8").read()
        rel = os.path.basename(path)
        assert not guid.search(text), f"{rel} carries a GUID"
        assert not email.search(text), f"{rel} carries an e-mail address"
        assert "://" not in text and "sharepoint.com" not in text.lower(), f"{rel} carries a URL"


def test_the_app_object_routes_deep_links_and_declares_the_named_formulas():
    app = _load(os.path.join(SRC, "App.pa.yaml"))["App"]["Properties"]
    start = _code(app["StartScreen"])
    assert 'Param("screen")' in app["StartScreen"] and 'Param("approvalId")' in app["StartScreen"] and 'Param("repo")' in app["StartScreen"]
    for screen in ("ApprovalScreen", "AgentScreen", "HomeScreen"):
        assert screen in start
    assert app["BackEnabled"] == "=true"
    assert "Trace(" in app["OnError"] and "FirstError" in app["OnError"]
    assert "OnStart" not in app, "initialisation lives in Formulas and StartScreen, never OnStart"
    formulas = app["Formulas"]
    assert formulas.startswith("=")
    declared = set(re.findall(r"^\s*([A-Z]\w*)\s*=", formulas, re.M))
    for name in ("Operator", "Heartbeat", "HeartbeatAgeSeconds", "LaptopStale", "OperatorMismatch", "ExpireSeconds",
                 "PendingApprovals", "PendingCount", "NeedsYou", "DeepLinkApproval", "DeepLinkAgent", "IsPhone",
                 "IsWide", "AppVersion"):
        assert name in declared, f"App.Formulas does not declare {name}"
    assert "3 * HeartbeatEverySeconds" in formulas, "the one threshold the app owns: 3 x EverySeconds"
    assert "Coalesce(Value(Heartbeat.ExpireSeconds), 900)" in formulas
    assert not re.search(r"\b(Set|Navigate|Notify|Refresh|Patch|Collect)\(", formulas), "named formulas cannot behave"


def test_every_screen_is_one_scrolling_root_container_sized_to_the_app():
    for screen, body in _screens().items():
        props = body.get("Properties") or {}
        assert props.get("Width") == "=Max(App.Width, App.MinScreenWidth)", screen
        assert props.get("Height") == "=Max(App.Height, App.MinScreenHeight)", screen
        assert props.get("LoadingSpinner") == "=LoadingSpinner.Controls", screen
        children = body.get("Children") or []
        assert len(children) == 1, f"{screen}: one root container, nothing beside it"
        (name, root), = children[0].items()
        assert root["Control"] == "GroupContainer" and root.get("Variant") == "AutoLayout", f"{screen}/{name}"
        rp = root["Properties"]
        assert rp["Width"] == "=Parent.Width" and rp["Height"] == "=Parent.Height", f"{screen}/{name}"
        assert rp["LayoutMinWidth"] == "=0" and rp["LayoutMinHeight"] == "=0", f"{screen}/{name}"
        assert rp["LayoutOverflowY"] == "=LayoutOverflow.Scroll", f"{screen}/{name}"
        assert rp["LayoutJustifyContent"] == "=LayoutJustifyContent.Start", f"{screen}/{name}: scroll needs Start"
        first = next(iter(root["Children"][0].values()))
        assert first.get("ComponentName") == "FleetHeader", f"{screen}: the header comes first"


def test_fixed_size_children_of_autolayout_containers_set_fill_portions():
    """Along a container's own axis, a child with a literal size says `FillPortions: =0`, or the
    container silently overrides the size (the plugin's layout guide); across the axis the size is
    the container's business (`LayoutAlignItems`). And every AutoLayout container zeroes the minimum
    sizes, whose defaults of 250 and 100 break a phone."""
    for owner, name, control, parent, _ in _all_controls():
        props = control.get("Properties") or {}
        if _type(control) == "GroupContainer" and control.get("Variant") == "AutoLayout":
            assert props.get("LayoutMinWidth") == "=0" and props.get("LayoutMinHeight") == "=0", (
                f"{owner}/{name}: the defaults are 250 and 100, which break phones")
            assert props.get("LayoutDirection") in ("=LayoutDirection.Vertical", "=LayoutDirection.Horizontal"), f"{owner}/{name}"
        if not parent or parent.get("Variant") != "AutoLayout":
            continue
        axis = "Width" if parent["Properties"]["LayoutDirection"] == "=LayoutDirection.Horizontal" else "Height"
        assert "FillPortions" in props, f"{owner}/{name}: every child of an AutoLayout container says its FillPortions"
        if _number(props.get(axis)) is not None:
            assert props["FillPortions"] == "=0", f"{owner}/{name}: a literal {axis} needs FillPortions =0"


def test_gallery_rows_are_one_autolayout_container_sized_to_the_template():
    galleries = [(o, n, c) for o, n, c, _, _ in _all_controls() if _type(c) == "Gallery"]
    assert len(galleries) >= 5
    for owner, name, gallery in galleries:
        assert gallery.get("Variant") == "Vertical", f"{owner}/{name}"
        props = gallery["Properties"]
        assert _number(props.get("TemplateSize")) >= 88, f"{owner}/{name}: rows are at least 88 high"
        assert _number(props.get("TemplatePadding")) >= 8, f"{owner}/{name}"
        assert props.get("DelayItemLoading") == "=true" and props.get("LoadingSpinner") == "=LoadingSpinner.Data", f"{owner}/{name}"
        children = gallery.get("Children") or []
        assert len(children) == 1, f"{owner}/{name}: exactly one row container"
        (row_name, row), = children[0].items()
        assert row["Control"] == "GroupContainer" and row.get("Variant") == "AutoLayout", f"{owner}/{row_name}"
        assert row["Properties"]["Width"] == "=Parent.TemplateWidth" and row["Properties"]["Height"] == "=Parent.TemplateHeight"
        for _, inner, _, _ in _controls(children):
            assert inner["Control"] != "CanvasComponent", f"{owner}/{name}: a component cannot live in a gallery"


def test_badges_colour_by_a_closed_set_and_nothing_parses_a_state_name():
    badges = [(o, n, c) for o, n, c, _, _ in _all_controls() if _type(c) == "Badge"]
    assert badges, "no Badge in the app"
    for owner, name, badge in badges:
        theme = badge["Properties"]["ThemeColor"]
        m = re.match(r"=Switch\((ThisItem|selAttention|selApproval)\.(Role|Status|Severity), ", theme)
        assert m, f"{owner}/{name}: ThemeColor must be a Switch over Role, Status or Severity: {theme[:60]!r}"
        assert "'BadgeCanvas.ThemeColor'." in theme
        assert badge["Properties"].get("AccessibleLabel", "").startswith("=")
    for owner, holder, prop, formula in _formulas():
        code = _code(formula)
        assert not re.search(r"\bState\s*(=|<>|in\b)", code), f"{owner}/{holder}.{prop} decides on a state name"
        assert not re.search(r"(StartsWith|EndsWith|Find|Match)\([^)]*\bState\b", code), f"{owner}/{holder}.{prop}"


def test_text_sizes_keep_the_floor():
    for owner, name, control, _, _ in _all_controls():
        if _type(control) != "ModernText":
            continue
        size = _number((control.get("Properties") or {}).get("Size"))
        assert size is not None, f"{owner}/{name}: set Size explicitly (the default is 15)"
        floor = 13 if name == "lblApprovalPayload" else 14
        assert size >= floor, f"{owner}/{name}: Size {size} is under {floor}"


def test_selection_uses_set_and_the_approval_buttons_are_gated_on_pending_and_expiry():
    formulas = list(_formulas())
    assert not any("UpdateContext(" in _code(f) for _, _, _, f in formulas), "one convention: Set"
    for var in ("selAttention", "selApproval", "decideChoice", "busy"):
        assert any(re.search(rf"\bSet\({var},", _code(f)) for _, _, _, f in formulas), f"{var} is never set"
    approval = {n: c for o, n, c, _, _ in _all_controls() if o == "ApprovalScreen"}
    gate = '=If(selApproval.Status = "pending" && DateTimeValue(selApproval.Expires) > Now(), DisplayMode.Edit, DisplayMode.Disabled)'
    for button in ("btnApprove", "btnDeny"):
        assert approval[button]["Properties"]["DisplayMode"] == gate, button
        assert _number(approval[button]["Properties"]["Height"]) == 52
    assert 'Set(decideChoice, "approved")' in approval["btnApprove"]["Properties"]["OnSelect"]
    assert 'Set(decideChoice, "denied")' in approval["btnDeny"]["Properties"]["OnSelect"]
    decide = {n: c for o, n, c, _, _ in _all_controls() if o == "DecideScreen"}
    assert 'decideChoice = "denied" && IsBlank(Trim(txtReason.Text))' in decide["btnDecideSend"]["Properties"]["DisplayMode"]


# ---------------------------------------------------------------------------- theme and samples


def test_the_theme_is_the_documented_paste_shape_without_comments():
    raw = open(THEME, encoding="utf-8").read()
    assert not any(line.lstrip().startswith("#") for line in raw.splitlines()), "the Themes pane is not documented to take comments"
    themes = yaml.safe_load(raw)
    assert list(themes) == ["Themes"] and list(themes["Themes"]) == ["FleetTheme"]
    theme = themes["Themes"]["FleetTheme"]
    assert set(theme) <= {"Font", "BasePaletteColor", "HueTorsion", "Vibrancy", "ColorOverrides"}
    assert {"Font", "BasePaletteColor", "HueTorsion", "Vibrancy"} <= set(theme)
    assert re.fullmatch(r"#[0-9A-Fa-f]{6}", theme["BasePaletteColor"])
    assert -100 <= theme["HueTorsion"] <= 100 and -100 <= theme["Vibrancy"] <= 100
    from agentdata.theme import DARK
    assert theme["BasePaletteColor"].upper() == DARK.accent.upper(), "the seed is the desk's dark palette accent"


def test_the_schema_copy_is_the_official_v3_schema_and_the_note_says_so():
    schema = _load(SCHEMA)
    assert schema["$id"] == "http://powerapps.com/schemas/pa-yaml/v3.0/pa.schema"
    assert "ControlTypeId-pattern" in schema["definitions"]
    with open(SCHEMA, encoding="utf-8") as f:
        assert sum(1 for _ in f) == 584, "the copy must stay unmodified; replace it whole and update LICENSE-NOTE.md"
    note = open(os.path.join(MOBILE, "schema", "LICENSE-NOTE.md"), encoding="utf-8").read()
    assert "MIT" in note and "PowerApps-Tooling" in note and "schemas/pa-yaml/v3.0" in note and "2026-09-26" in note


def test_the_sample_rows_keep_the_contract_and_carry_no_secrets():
    files = sorted(glob.glob(os.path.join(SAMPLE, "*.json")))
    assert sorted(os.path.basename(f)[:-5] for f in files) == sorted(LISTS)
    for path in files:
        table = os.path.basename(path)[:-5]
        rows = json.load(open(path, encoding="utf-8"))
        assert isinstance(rows, list) and rows, table
        assert len(rows) == 1 if table == "FleetHeartbeat" else 3 <= len(rows) <= 5, f"{table}: {len(rows)} rows"
        titles = [r["Title"] for r in rows]
        assert all(titles) and len(set(titles)) == len(titles), f"{table}: Title is the key"
        for row in rows:
            assert list(row) == COLUMNS[table], f"{table}: columns drifted from the contract: {list(row)}"
            for column, value in row.items():
                assert isinstance(value, str), f"{table}.{column}: every list column is text"
                assert not LEAK.search(value), f"{table}.{column} leaks: {value[:60]!r}"
                if column in STAMP_COLUMNS and value:
                    assert STAMP.match(value), f"{table}.{column}: {value!r} is not YYYY-MM-DDTHH:MM:SSZ"
                if (table, column) in BOOLEANS and value:
                    assert value in ("true", "false"), f"{table}.{column}: {value!r}"
                closed = CLOSED_SETS.get((table, column))
                if closed is not None:
                    assert value in closed, f"{table}.{column}: {value!r} is outside {sorted(closed)}"
            if table == "FleetAttention":
                assert row["Role"] == STATE_ROLES[row["State"]], f"{row['Title']}: Role is the server's map of State"
                assert row["NeedsHuman"] == str(needs_the_human(row["State"])).lower(), row["Title"]
                json.loads(row["QuestionsJson"]); json.loads(row["ApprovalsJson"])
            if table == "FleetApprovals" and row["Status"] == "denied":
                assert row["Reason"], "a denial requires a reason"
    approvals = json.load(open(os.path.join(SAMPLE, "FleetApprovals.json"), encoding="utf-8"))
    pending = [r for r in approvals if r["Status"] == "pending"]
    assert pending and all(r["ApprovalKind"] == "jira-transition" and '"dry_run": true' in r["PayloadPreview"] for r in pending)


def test_the_mobile_files_are_utf8_lf_without_trailing_whitespace():
    """The app's own files only: `mobile/data/` and `mobile/flows/` belong to other lanes."""
    paths = [os.path.join(REPO_ROOT, "mobile", "README.md")] + glob.glob(os.path.join(MOBILE, "**", "*"), recursive=True)
    checked = 0
    for path in paths:
        if not path.endswith((".yaml", ".json", ".md")) or path.endswith("pa.schema.yaml"):
            continue
        raw = open(path, "rb").read()
        text = raw.decode("utf-8")
        rel = os.path.relpath(path, REPO_ROOT)
        assert b"\r" not in raw, f"{rel}: CRLF"
        assert text.endswith("\n"), f"{rel}: no final newline"
        for n, line in enumerate(text.split("\n"), 1):
            assert line == line.rstrip(), f"{rel}:{n}: trailing whitespace"
        checked += 1
    assert checked >= 20
