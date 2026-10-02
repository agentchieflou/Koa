"""The pinned mobile contract, for tests: `contract/PIN` read, the schema loaded once, a validator per `$defs`
record, the examples by file name, and the flow definitions' actions by name.

This is the consumer's copy of the helper the laptop keeps in this-next-please (`tests/mobile_contract.py`), minus
everything that needs the bridge: Koa reads the contract, never the `agentdata` package.
"""
from __future__ import annotations
import functools
import glob
import json
import os
import re

from jsonschema import Draft202012Validator

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRACT_DIR = os.path.join(REPO_ROOT, "contract")
PIN_PATH = os.path.join(CONTRACT_DIR, "PIN")
EXAMPLES = os.path.join(CONTRACT_DIR, "examples")
FLOWS = os.path.join(REPO_ROOT, "flows")

#: What the laptop writes, by `$defs` name: the record kinds of the outbox and `pairing.json`.
OUTBOX_DEFS = ("attention", "approval", "decision_mirror", "notification", "heartbeat", "result", "pairing")
#: What FleetDecide writes into `inbox/`.
INBOX_DEFS = ("inbox_decision", "inbox_reply")
RECORDS = OUTBOX_DEFS + INBOX_DEFS

_HASH_LINE = re.compile(r"^([0-9a-f]{64})  (\S.*)$")
_KEY_LINE = re.compile(r"^([a-z_]+): (.+)$")


@functools.lru_cache(maxsize=None)
def pin() -> dict:
    """`{"keys": {tag, source, contract}, "files": {relative path: sha256}}` from `contract/PIN`."""
    keys, files = {}, {}
    with open(PIN_PATH, encoding="utf-8") as f:
        for n, line in enumerate(f.read().split("\n"), 1):
            if not line or line.startswith("#"):
                continue
            if m := _HASH_LINE.match(line):
                files[m.group(2)] = m.group(1)
            elif m := _KEY_LINE.match(line):
                keys[m.group(1)] = m.group(2)
            else:
                raise AssertionError(f"contract/PIN:{n}: neither `key: value` nor `<sha256>  <path>`: {line!r}")
    return {"keys": keys, "files": files}


def schema_path() -> str:
    return os.path.join(CONTRACT_DIR, f"fleet-mobile.v{pin()['keys']['contract']}.schema.json")


@functools.lru_cache(maxsize=None)
def load() -> dict:
    with open(schema_path(), encoding="utf-8") as f:
        return json.load(f)


def defs() -> dict:
    return load()["$defs"]


@functools.lru_cache(maxsize=None)
def validator(name: str) -> Draft202012Validator:
    """A validator for one `$defs` entry, resolved against the whole file."""
    schema = load()
    return Draft202012Validator({"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": f"#/$defs/{name}"})


def errors(record, name: str) -> list[str]:
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '<record>'}: {e.message}"
            for e in validator(name).iter_errors(record)]


def check(record, name: str, where: str = "") -> None:
    found = errors(record, name)
    assert not found, f"{where or name} breaks the mobile contract ({name}):\n  " + "\n  ".join(found)


def resolve(node: dict) -> dict:
    """A schema node with its `$ref` (to `#/$defs/...`) followed."""
    while isinstance(node, dict) and "$ref" in node:
        node = defs()[node["$ref"].rsplit("/", 1)[-1]]
    return node


def example_def(path: str, record: dict) -> str:
    """The `$defs` name an example is an instance of: `inbox-*` files are FleetDecide's, the rest the laptop's."""
    kind = record["kind"]
    if os.path.basename(path).startswith("inbox-"):
        return "inbox_" + kind
    return "decision_mirror" if kind == "decision" else kind


def examples() -> dict[str, dict]:
    out = {}
    for path in sorted(glob.glob(os.path.join(EXAMPLES, "*.json"))):
        with open(path, encoding="utf-8") as f:
            out[os.path.basename(path)] = json.load(f)
    return out


def flow(name: str) -> dict:
    with open(os.path.join(FLOWS, f"{name}.definition.json"), encoding="utf-8") as f:
        return json.load(f)


def actions(node) -> dict:
    """Every action of a flow definition by name, however deep the scopes, conditions and switch cases nest."""
    found = {}
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "actions" and isinstance(value, dict):
                found.update(value)
            found.update(actions(value))
    elif isinstance(node, list):
        for value in node:
            found.update(actions(value))
    return found
