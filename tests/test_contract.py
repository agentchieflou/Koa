"""The consumer's side of the mobile contract (this-next-please#600): Koa builds to `contract/fleet-mobile.v1.schema.json`
as pinned by `contract/PIN`, and these tests hold the pin, the examples, the five lists, `FleetDecide`'s signature and
the workbook to it. The laptop holds its own side in this-next-please (`tests/test_mobile_contract.py`); the two meet
only at the pinned file, so a change on either side that the other has not taken fails here or there, never on the
phone.
"""
from __future__ import annotations
import glob
import hashlib
import importlib.util
import json
import os
import re
import zipfile

from jsonschema import Draft202012Validator

import koa_contract as KC
from test_mobile_powerapp import COLUMNS, LISTS, SAMPLE


# ------------------------------------------------------------------------------------ the pin


def test_every_contract_file_hashes_to_its_pin_line_and_every_file_is_pinned():
    pinned = KC.pin()["files"]
    on_disk = {os.path.relpath(p, KC.CONTRACT_DIR).replace(os.sep, "/")
               for p in glob.glob(os.path.join(KC.CONTRACT_DIR, "**", "*"), recursive=True)
               if os.path.isfile(p) and os.path.basename(p) != "PIN"}
    assert set(pinned) == on_disk, "contract/ and contract/PIN disagree on which files are pinned"
    for rel, want in pinned.items():
        with open(os.path.join(KC.CONTRACT_DIR, rel), "rb") as f:
            got = hashlib.sha256(f.read()).hexdigest()
        assert got == want, (f"contract/{rel} is not the pinned file (sha256 {got}, PIN says {want}): replace the "
                             "contract only from a published mobile-contract tag, files and PIN together")


def test_the_pin_names_a_tag_a_source_commit_and_the_schemas_own_version():
    keys = KC.pin()["keys"]
    assert re.fullmatch(r"mobile-contract-v\d+", keys["tag"]), keys
    assert re.fullmatch(r"agentchieflou/this-next-please@[0-9a-f]{40}", keys["source"]), keys
    assert keys["tag"] == f"mobile-contract-v{keys['contract']}"
    assert os.path.basename(KC.schema_path()) in KC.pin()["files"]
    schema = KC.load()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["contract"] == int(keys["contract"]) == KC.defs()["contract"]["const"]
    Draft202012Validator.check_schema(schema)


def test_the_contract_files_are_utf8_lf_without_a_bom():
    for path in glob.glob(os.path.join(KC.CONTRACT_DIR, "**", "*"), recursive=True):
        if os.path.isfile(path):
            raw = open(path, "rb").read()
            assert b"\r" not in raw and raw.endswith(b"\n") and not raw.startswith(b"\xef\xbb\xbf"), path


def test_nothing_here_imports_the_laptops_package():
    """Koa never imports `agentdata` (#600): the laptop's vocabulary arrives through the contract only."""
    importing = re.compile(r"^\s*(from\s+agentdata\b|import\s+agentdata\b)|import_module\(\s*[\"']agentdata", re.M)
    offenders = []
    for path in glob.glob(os.path.join(KC.REPO_ROOT, "**", "*.py"), recursive=True):
        if os.sep + ".git" + os.sep in path:
            continue
        if importing.search(open(path, encoding="utf-8").read()):
            offenders.append(os.path.relpath(path, KC.REPO_ROOT))
    assert offenders == []


# ------------------------------------------------------------------------------------ the examples


def test_every_example_validates_and_there_is_one_per_record_kind():
    root = Draft202012Validator(KC.load())
    covered = set()
    for name, record in KC.examples().items():
        which = KC.example_def(name, record)
        KC.check(record, which, where=f"contract/examples/{name}")
        assert not list(root.iter_errors(record)), f"{name}: the root schema does not accept it as exactly one kind"
        covered.add(which)
    assert covered == set(KC.RECORDS)


def test_each_inbox_example_is_what_fleet_decide_composes():
    examples = KC.examples()
    actions = KC.actions(KC.flow("FleetDecide"))
    for name, action in (("inbox-decision-9f2c4b7e.json", "Compose_decision_record"),
                         ("inbox-reply-4b8e1f3a.json", "Compose_reply_record")):
        assert list(examples[name]) == list(actions[action]["inputs"]), name


def test_a_reply_is_a_message_or_answers_and_never_empty():
    """The prompt the phone sends: the contract refuses a reply with nothing in it, as the laptop does."""
    reply = KC.examples()["inbox-reply-4b8e1f3a.json"]          # answers, and an empty message
    prompt = dict(reply, message="Run the UAT again on the October extract.", answers=None)
    assert not KC.errors(prompt, "inbox_reply"), "a message alone is a reply"
    assert not KC.errors(dict(reply, message=None), "inbox_reply"), "answers alone are a reply"
    assert KC.errors(dict(prompt, message="   "), "inbox_reply"), "a blank message says nothing"
    assert KC.errors(dict(reply, message="", answers=[{"id": "q1", "answer": " "}]), "inbox_reply"), "nor a blank answer"
    assert not KC.errors(dict(prompt, message="x" * 4000), "inbox_reply")
    assert KC.errors(dict(prompt, message="x" * 4001), "inbox_reply"), "4000 characters at most"
    assert KC.errors({k: v for k, v in reply.items() if k != "repo"}, "inbox_reply"), "a reply names its repo"


# ------------------------------------------------------------------------------------ the lists and the flow


def test_the_five_lists_are_the_apps_columns_and_every_sample_row_validates():
    defs = KC.defs()
    assert set(LISTS) == set(COLUMNS)
    for table in LISTS:
        assert list(defs[table]["properties"]) == COLUMNS[table], table
        optional = set(defs[table]["properties"]) - set(defs[table]["required"])
        assert optional == (set() if table == "FleetHeartbeat" else {"Operator"}), f"{table}: {optional}"
        assert defs[table]["required"] == [c for c in COLUMNS[table] if c not in optional], table
        with open(os.path.join(SAMPLE, f"{table}.json"), encoding="utf-8") as f:
            for row in json.load(f):
                KC.check(row, table, where=f"powerapp/sample/{table}.json {row['Title']}")


def test_fleet_decides_inputs_and_response_are_the_contracts():
    defs = KC.defs()
    flow = KC.flow("FleetDecide")["properties"]["definition"]
    trigger = flow["triggers"]["manual"]["inputs"]["schema"]
    titles = [p["title"] for p in trigger["properties"].values()]
    assert titles == list(defs["fleet_decide_inputs"]["properties"]) == defs["fleet_decide_inputs"]["required"]
    for key, prop in trigger["properties"].items():
        want = defs["fleet_decide_inputs"]["properties"][prop["title"]]
        assert ("number" if key.startswith("number") else "string") == want.get("type", "string"), prop["title"]
    responses = [a for a in KC.actions(flow).values() if a.get("type") == "Response"]
    assert len(responses) == 3
    for response in responses:
        assert list(response["inputs"]["body"]) == list(defs["fleet_decide_response"]["properties"])


def test_the_app_calls_fleet_decide_with_the_contracts_arguments_in_order():
    """`FleetDecide.Run(...)` in the app passes the trigger's inputs positionally: the count must be the contract's."""
    want = len(KC.defs()["fleet_decide_inputs"]["properties"])
    calls = 0
    for path in glob.glob(os.path.join(KC.REPO_ROOT, "powerapp", "src", "**", "*.pa.yaml"), recursive=True):
        text = open(path, encoding="utf-8").read()
        for start in (m.end() for m in re.finditer(r"FleetDecide\.Run\(", text)):
            depth, args, i = 1, 1, start
            while depth:
                c = text[i]
                if c == '"':
                    i = text.index('"', i + 1)
                elif c in "([{":
                    depth += 1
                elif c in ")]}":
                    depth -= 1
                elif c == "," and depth == 1:
                    args += 1
                i += 1
            assert args == want, f"{os.path.relpath(path, KC.REPO_ROOT)}: FleetDecide.Run with {args} arguments, the contract has {want}"
            calls += 1
    assert calls >= 2, "the decision and the reply both go through FleetDecide.Run"


# ------------------------------------------------------------------------------------ the workbook


def _workbook():
    """`data/make_workbook.py` as a module: its `ROWS` import without openpyxl, which only building needs."""
    path = os.path.join(KC.REPO_ROOT, "data", "make_workbook.py")
    spec = importlib.util.spec_from_file_location("make_workbook", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _cell(value) -> str:
    """A record value as FleetOutboxToLists writes it into a text column (`@string(...)` for objects and lists)."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    return "" if value is None else str(value)


def _result_columns(result: dict) -> dict:
    """The `result` case: `Result` from ok, `ResultText` = trim(concat(error, ' ', hint)) truncated to 255."""
    return {"Result": "applied" if result["ok"] else "rejected", "ResultCode": result["code"],
            "ResultText": f"{result['error']} {result['hint']}".strip()[:255], "ResultAt": result["at"]}


def test_the_workbooks_sample_rows_are_what_the_flows_write_from_the_contract_examples():
    """`data/README.md`: the rows are what `contract/examples/*.json` would have produced, column by column, by the
    mapping in `flows/README.md`. Every row is also a valid list row."""
    ex, rows = KC.examples(), _workbook().ROWS

    def row(table, title):
        [found] = [r for r in rows[table] if r["Title"] == title]
        return found

    a = ex["attention-luna-187.json"]
    want = {"FleetAttention": {a["repo"]: {
        "Title": a["repo"], "Project": a["project"], "Ticket": a["ticket"], "State": a["state"], "Role": a["role"],
        "NeedsHuman": _cell(a["needs_human"]), "Says": a["says"], "LastSaid": a["last_said"],
        "AgeSeconds": _cell(a["age_s"]), "At": a["at"], "Generated": a["generated"], "ApprovalId": a["approval_id"],
        "ApprovalsJson": _cell(a["approvals"]), "QuestionsJson": _cell(a["questions"]),
        "RunNumber": _cell(a["run"]["n"]), "RunOrigin": a["run"]["origin"], "RunLive": _cell(a["run"]["live"]),
        "Model": a["model"], "SpendLine": a["spend"]["line"], "SpendTotal": _cell(a["spend"]["total"]),
        "SpendToday": _cell(a["spend"]["today"]), "SpendBudget": _cell(a["spend"]["budget"]),
        "Turns": _cell(a["spend"]["turns"]), "Supervised": _cell(a["supervised"]), "External": _cell(a["external"]),
        "Digest": a["digest"], "Seq": _cell(a["seq"])}}}

    p, m = ex["approval-rdsd-uat-7f3a.json"], ex["decision-luna-a1c9.json"]
    want["FleetApprovals"] = {
        p["id"]: {"Title": p["id"], "Repo": p["repo"], "Ticket": p["ticket"], "ApprovalKind": p["approval_kind"],
                  "Summary": p["summary"], "PayloadPreview": _cell(p["payload_preview"]),
                  "PayloadTruncated": _cell(p["payload_truncated"]), "PayloadBytes": _cell(p["payload_bytes"]),
                  "Digest": p["digest"], "Created": p["created"], "Expires": p["expires"],
                  "WaitingSeconds": _cell(p["waiting_s"]), "Status": "pending", "DecidedBy": "", "DecidedAt": "",
                  "Reason": "", "Via": "", "Late": "", "Nonce": "", "ResultCode": "", "ResultText": "",
                  "SourceFile": p["id"] + ".json"},
        m["id"]: {"Title": m["id"], "Status": m["decision"], "DecidedBy": m["by"], "DecidedAt": m["decided"],
                  "Via": m["via"], "Late": _cell(m["late"]), "Reason": m["reason"], "Nonce": m["nonce"],
                  "Digest": m["digest"]},
    }

    d, r = ex["inbox-decision-9f2c4b7e.json"], ex["inbox-reply-4b8e1f3a.json"]
    applied, rejected = ex["result-9f2c4b7e.json"], ex["result-c0d3e6f9-rejected.json"]
    want["FleetDecisions"] = {
        d["nonce"]: {"Title": d["nonce"], "Kind": d["kind"], "ApprovalId": d["id"], "Decision": d["decision"],
                     "Reason": d["reason"], "Message": "", "AnswersJson": "", "Digest": d["digest"], "By": d["by"],
                     "Device": d["device"], "Issued": d["issued"], "Expires": d["expires"],
                     "InboxFile": f"{d['kind']}-{d['nonce']}.json", **_result_columns(applied)},
        # The reply row is FleetDecide's, before its result lands: `sent`, the result columns empty.
        r["nonce"]: {"Title": r["nonce"], "Kind": r["kind"], "ApprovalId": "", "Repo": r["repo"], "Decision": "",
                     "Reason": "", "Message": r["message"], "AnswersJson": _cell(r["answers"]), "Digest": "",
                     "By": r["by"], "Device": r["device"], "Issued": r["issued"], "Expires": r["expires"],
                     "InboxFile": f"{r['kind']}-{r['nonce']}.json", "Result": "sent", "ResultCode": "",
                     "ResultText": "", "ResultAt": ""},
        rejected["nonce"]: {"Title": rejected["nonce"], "Kind": rejected["kind_of"], "ApprovalId": rejected["id"],
                            **_result_columns(rejected)},
    }
    assert d["id"] == applied["id"] == m["id"] and d["nonce"] == applied["nonce"] == m["nonce"]
    assert m["decided"] == applied["at"], "the phone's decision is applied when it is decided"

    n = ex["notification-luna-needs_human-187.json"]
    want["FleetNotifications"] = {n["key"]: {
        "Title": n["key"], "Repo": n["repo"], "Ticket": n["ticket"], "State": n["state"], "Severity": n["severity"],
        "TitleText": n["title"], "Body": n["body"], "At": n["at"], "Seq": _cell(n["seq"]), "Quiet": _cell(n["quiet"]),
        "ApprovalId": n["approval_id"]}}

    h = ex["heartbeat-20260926-0915.json"]
    beat = {"Title": h["operator"], "At": h["at"], "EverySeconds": _cell(h["every_s"]),
            "ExpireSeconds": _cell(h["expire_s"]), "Contract": _cell(h["contract"]), "Operator": h["operator"],
            "Bridge": h["bridge"], "LaptopId": h["laptop_id"], "ServeUp": _cell(h["serve_up"]),
            "DeskStreams": _cell(h["desk_streams"]), "Repos": _cell(h["counts"]["repos"]),
            "NeedsHuman": _cell(h["counts"]["needs_human"]), "ApprovalsPending": _cell(h["counts"]["approvals_pending"]),
            "Notifications24h": _cell(h["counts"]["notifications_24h"]),
            "Rejected24h": _cell(h["counts"]["rejected_24h"]), "InboxLastSeen": h["inbox_last_seen"]}
    assert [b for b in rows["FleetHeartbeat"] if b["At"] == h["at"]] == [beat]

    for by_title in want.values():                          # every row names its operator, from the flow's config
        for columns in by_title.values():
            columns["Operator"] = h["operator"]

    off = [f"{table} {title} {c}: {row(table, title)[c]!r}, the example says {v!r}"
           for table, by_title in want.items() for title, columns in by_title.items()
           for c, v in columns.items() if row(table, title)[c] != v]
    assert off == [], "the workbook disagrees with contract/examples/:\n" + "\n".join(off)
    for table in LISTS:
        for sample in rows[table]:
            KC.check(sample, table, where=f"data/make_workbook.py {table} {sample['Title']}")


def _letter(i: int) -> str:
    """Excel's column letters: 1 -> A, 27 -> AA."""
    out = ""
    while i:
        i, rest = divmod(i - 1, 26)
        out = chr(65 + rest) + out
    return out


def test_the_committed_workbook_holds_exactly_the_generators_rows():
    """`FleetAgent.xlsx` is `make_workbook.py`'s output, sheet by sheet and cell by cell. Read with the standard
    library (openpyxl writes every cell as an inline string), so the check runs without openpyxl."""
    import xml.etree.ElementTree as ET
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    wb = _workbook()
    with zipfile.ZipFile(wb.OUT) as z:
        names = [e.get("name") for e in ET.fromstring(z.read("xl/workbook.xml")).iterfind("m:sheets/m:sheet", ns)]
        assert names == list(wb.COLUMNS)
        for n, table in enumerate(names, start=1):
            grid = []
            for r in ET.fromstring(z.read(f"xl/worksheets/sheet{n}.xml")).iterfind("m:sheetData/m:row", ns):
                cells = {re.match(r"[A-Z]+", c.get("r")).group(): "".join(t.text or "" for t in c.iterfind(".//m:t", ns))
                         for c in r.iterfind("m:c", ns)}
                grid.append(cells)
            columns = wb.COLUMNS[table]
            letters = [_letter(i) for i in range(1, len(columns) + 1)]
            got = [[g.get(x, "") for x in letters] for g in grid]
            assert got == [columns] + [[row[c] for c in columns] for row in wb.ROWS[table]], \
                f"{table}: FleetAgent.xlsx is stale; run python data/make_workbook.py"
