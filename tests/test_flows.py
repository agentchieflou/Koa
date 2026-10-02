"""The two flows against the pinned contract (this-next-please#600): every Parse JSON action accepts every pinned
example, and every field `FleetOutboxToLists` reads from the parsed record is one the contract defines.

Parse JSON in Power Automate validates with a draft-4 style schema and fails the run on a mismatch, so a record the
laptop is allowed to write but the flow's schema refuses is a run that never reaches a list: the phone would show
nothing, with no error anywhere but the flow's run history. These tests find that here instead.
"""
from __future__ import annotations
import json
import re

import pytest
from jsonschema import Draft4Validator

import koa_contract as KC

FLOW_NAMES = ("FleetOutboxToLists", "FleetDecide")
#: `body('Parse_JSON')?['a']?['b']`: a field path the flow reads from the parsed outbox record.
READ = re.compile(r"body\('Parse_JSON'\)((?:\?\['[A-Za-z0-9_]+'\])+)")


def _parse_json_actions() -> list[tuple[str, str, dict]]:
    found = []
    for flow in FLOW_NAMES:
        for name, action in KC.actions(KC.flow(flow)).items():
            if action.get("type") == "ParseJson":
                found.append((flow, name, action["inputs"]["schema"]))
    return found


def test_the_outbox_flow_parses_every_file_with_one_parse_json_action():
    assert [(f, n) for f, n, _ in _parse_json_actions()] == [("FleetOutboxToLists", "Parse_JSON")]


@pytest.mark.parametrize("example", sorted(KC.examples()))
def test_every_parse_json_schema_accepts_every_pinned_example(example):
    record = KC.examples()[example]
    for flow, name, schema in _parse_json_actions():
        Draft4Validator.check_schema(schema)
        found = [f"{'/'.join(str(p) for p in e.absolute_path) or '<record>'}: {e.message}"
                 for e in Draft4Validator(schema).iter_errors(record)]
        assert not found, f"{flow}.{name} would fail the run on contract/examples/{example}:\n  " + "\n  ".join(found)


def test_every_optional_field_may_be_absent_or_null_for_parse_json():
    """The contract adds optional fields without a version bump; Parse JSON must not require any field but `kind`,
    and every declared field must take `null`, or an older or newer laptop's record fails the run."""
    for flow, name, schema in _parse_json_actions():
        assert set(schema.get("required", [])) <= {"kind"}, f"{flow}.{name} requires {schema.get('required')}"

        def walk(node, path):
            for key, prop in (node.get("properties") or {}).items():
                types = prop.get("type")
                types = [types] if isinstance(types, str) else list(types or [])
                assert "null" in types or path + key == "kind", f"{flow}.{name}: {path}{key} does not take null"
                assert not prop.get("required"), f"{flow}.{name}: {path}{key} requires {prop['required']}"
                if "properties" in prop:
                    walk(prop, f"{path}{key}.")
                if isinstance(prop.get("items"), dict) and "properties" in prop["items"]:
                    walk(prop["items"], f"{path}{key}[].")

        walk(schema, "")


def _contract_has(path: list[str]) -> bool:
    """Whether some outbox record kind in the contract defines this nested field path."""
    for kind in KC.OUTBOX_DEFS:
        node = KC.resolve(KC.defs()[kind])
        for key in path:
            props = (node or {}).get("properties") or {}
            if key not in props:
                node = None
                break
            node = KC.resolve(props[key])
        if node is not None:
            return True
    return False


def test_every_field_the_outbox_flow_reads_is_in_the_contract_and_in_its_parse_json_schema():
    text = json.dumps(KC.flow("FleetOutboxToLists"))
    paths = {tuple(re.findall(r"\['([A-Za-z0-9_]+)'\]", m.group(1))) for m in READ.finditer(text.replace("\\'", "'"))}
    assert len(paths) >= 40, f"only {len(paths)} field reads found: has the expression syntax changed?"
    [(_, _, schema)] = _parse_json_actions()
    for path in sorted(paths):
        assert _contract_has(list(path)), f"FleetOutboxToLists reads {'.'.join(path)}, which no outbox record has"
        node = schema
        for key in path:
            assert key in (node.get("properties") or {}), f"Parse_JSON's schema does not declare {'.'.join(path)}"
            node = node["properties"][key]
