#!/usr/bin/env python3
"""Build ``mobile/data/FleetAgent.xlsx``: five Excel tables that seed the five FleetAgent lists.

Run from the repository root::

    python mobile/data/make_workbook.py

One worksheet per list, each holding an Excel *table* of the same name (``FleetAttention`` ...) whose
header row is the contract's columns in order, followed by three sample rows. Two uses:

* Microsoft Lists > **Create a list** > **From Excel** reads the table and builds the list with the
  right columns (choose *Single line of text* for every column except the multi-line ones, see
  ``README.md`` beside this file).
* The same workbook is the Excel Online (Business) fallback store when no SharePoint site is available
  (``FleetAgent.xlsx`` written by FleetOutboxToLists, a copy ``FleetAgent-Decisions.xlsx`` written by
  FleetDecide -- one writer per workbook).

Deterministic: fixed dates, no random values, document properties pinned, zip entry timestamps pinned,
so re-running produces the same bytes and the committed file never churns. Needs ``openpyxl``
(``python -m pip install --user openpyxl``); it is not a project dependency. The check at the end
re-opens the produced file and asserts the tables and columns exist.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import os
import re
import shutil
import sys
import tempfile
import zipfile

try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.table import Table, TableStyleInfo
except ImportError:  # pragma: no cover - a message beats a traceback
    sys.exit("openpyxl is required: python -m pip install --user openpyxl")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "FleetAgent.xlsx")
FIXED_DATE = dt.datetime(2026, 9, 26, 0, 0, 0)
ZIP_DATE = (2026, 9, 26, 0, 0, 0)
OPERATOR = "operator@example.com"

# Contract v1: every column is text; the multi-line ones are listed in MULTILINE.
COLUMNS = {
    "FleetAttention": [
        "Title", "Project", "Ticket", "State", "Role", "NeedsHuman", "Says", "LastSaid", "AgeSeconds", "At",
        "Generated", "ApprovalId", "ApprovalsJson", "QuestionsJson", "RunNumber", "RunOrigin", "RunLive", "Model",
        "SpendLine", "SpendTotal", "SpendToday", "SpendBudget", "Turns", "Supervised", "External", "Digest", "Seq",
    ],
    "FleetApprovals": [
        "Title", "Repo", "Ticket", "ApprovalKind", "Summary", "PayloadPreview", "PayloadTruncated", "PayloadBytes",
        "Digest", "Created", "Expires", "WaitingSeconds", "Status", "DecidedBy", "DecidedAt", "Reason", "Via", "Late",
        "Nonce", "ResultCode", "ResultText", "SourceFile",
    ],
    "FleetDecisions": [
        "Title", "Kind", "ApprovalId", "Repo", "Decision", "Reason", "Message", "AnswersJson", "Digest", "By",
        "Device", "Issued", "Expires", "InboxFile", "Result", "ResultCode", "ResultText", "ResultAt",
    ],
    "FleetNotifications": [
        "Title", "Repo", "Ticket", "State", "Severity", "TitleText", "Body", "At", "Seq", "Quiet", "ApprovalId",
        "SourceFile",
    ],
    "FleetHeartbeat": [
        "Title", "At", "EverySeconds", "ExpireSeconds", "Contract", "Operator", "Bridge", "LaptopId", "ServeUp",
        "DeskStreams", "Repos", "NeedsHuman", "ApprovalsPending", "Notifications24h", "Rejected24h", "InboxLastSeen",
    ],
}
MULTILINE = {
    "FleetAttention": {"Says", "QuestionsJson"},
    "FleetApprovals": {"PayloadPreview"},
    "FleetDecisions": {"Message", "AnswersJson"},
    "FleetNotifications": {"Body"},
    "FleetHeartbeat": set(),
}

# Fictional sha256/nonce values (hex only; nothing here is derived from real data).
DIGEST_A = "3f9c1e8d2b7a4c6e5d0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d"
DIGEST_B = "7d2a9f4c6b1e8d3f5a0c2e4b6d8f1a3c5e7b9d0f2a4c6e8b1d3f5a7c9e0b2d4f"
DIGEST_C = "a1c9e2b4d6f8a0c2e4b6d8f0a2c4e6b8d0f2a4c6e8b0d2f4a6c8e0b2d4f6a8c0"
DIGEST_D = "e4b2d0f8a6c4e2b0d8f6a4c2e0b8d6f4a2c0e8b6d4f2a0c8e6b4d2f0a8c6e4b2"
NONCE_APPLIED = "9f2c4b7e1d3a48c2b6e5f0a1d2c3b4e5"
NONCE_REPLY = "4b8e1f3a9c2d47e6b0a5d9c8f7e6b5a4"
NONCE_REJECTED = "c0d3e6f9a2b5c8d1e4f7a0b3c6d9e2f5"
LAPTOP_ID = "5e1c9a7b3d2f4e6a8c0b1d3f5a7c9e2b"
APPROVAL_PENDING = "rdsd-uat-jira-transition-20260926T091200Z-7f3a"
APPROVAL_APPROVED = "luna-jira-create-20260925T160301Z-a1c9"
APPROVAL_DENIED = "dpm-reports-pncli-write-20260925T110000Z-33be"
APPROVAL_EXPIRED = "rdsd-uat-jira-transition-20260924T083000Z-0c4d"

ROWS = {
    "FleetAttention": [
        {
            "Title": "luna", "Project": "luna", "Ticket": "RDSD-118", "State": "needs_human", "Role": "human",
            "NeedsHuman": "true",
            "Says": "Two readings of the acceptance criteria lead to different work; asked which date window to use "
                    "and stopped.",
            "LastSaid": "Asked: calendar month or the last 30 days? Waiting for an answer.",
            "AgeSeconds": "412", "At": "2026-09-26T09:14:05Z", "Generated": "2026-09-26T09:14:06Z", "ApprovalId": "",
            "ApprovalsJson": "[]",
            "QuestionsJson": '[{"id":"q1","q":"Which date window: calendar month or the last 30 days?",'
                             '"choices":["calendar month","last 30 days"],"want":"choice","default":"calendar month"}]',
            "RunNumber": "3", "RunOrigin": "fleet", "RunLive": "true", "Model": "cli-auto",
            "SpendLine": "4.3 premium · of 10 · 12 turns", "SpendTotal": "4.3", "SpendToday": "1.2",
            "SpendBudget": "10", "Turns": "12", "Supervised": "true", "External": "false", "Digest": DIGEST_A,
            "Seq": "187",
        },
        {
            "Title": "rdsd-uat", "Project": "rdsd", "Ticket": "RDSD-131", "State": "waiting_approval",
            "Role": "waiting", "NeedsHuman": "true", "Says": "a write is waiting for one click",
            "LastSaid": "Dry run is green; the transition to In Review is waiting for approval.",
            "AgeSeconds": "125", "At": "2026-09-26T09:12:01Z", "Generated": "2026-09-26T09:12:02Z",
            "ApprovalId": APPROVAL_PENDING, "ApprovalsJson": '["%s"]' % APPROVAL_PENDING, "QuestionsJson": "[]",
            "RunNumber": "1", "RunOrigin": "console", "RunLive": "true", "Model": "cli-auto",
            "SpendLine": "1.1 premium · 4 turns", "SpendTotal": "1.1", "SpendToday": "1.1", "SpendBudget": "",
            "Turns": "4", "Supervised": "true", "External": "false", "Digest": DIGEST_B, "Seq": "42",
        },
        {
            "Title": "dpm-reports", "Project": "dpm", "Ticket": "DPM-77", "State": "running", "Role": "running",
            "NeedsHuman": "false", "Says": "a turn is in progress",
            "LastSaid": "Comparing the two extracts with ad-diff before writing the summary.",
            "AgeSeconds": "9", "At": "2026-09-26T09:14:50Z", "Generated": "2026-09-26T09:14:51Z", "ApprovalId": "",
            "ApprovalsJson": "[]", "QuestionsJson": "[]", "RunNumber": "2", "RunOrigin": "adopted", "RunLive": "true",
            "Model": "cli-auto", "SpendLine": "0.6 premium · of 5 · 3 turns", "SpendTotal": "0.6",
            "SpendToday": "0.6", "SpendBudget": "5", "Turns": "3", "Supervised": "false", "External": "true",
            "Digest": DIGEST_C, "Seq": "903",
        },
    ],
    "FleetApprovals": [
        {
            "Title": APPROVAL_PENDING, "Repo": "rdsd-uat", "Ticket": "RDSD-131", "ApprovalKind": "jira-transition",
            "Summary": "Transition RDSD-131 to In Review",
            "PayloadPreview": '{"key":"RDSD-131","transition":"In Review","comment":"PR #42 opened"}',
            "PayloadTruncated": "false", "PayloadBytes": "74", "Digest": DIGEST_B, "Created": "2026-09-26T09:12:00Z",
            "Expires": "2026-09-26T09:42:00Z", "WaitingSeconds": "125", "Status": "pending", "DecidedBy": "",
            "DecidedAt": "", "Reason": "", "Via": "", "Late": "", "Nonce": "", "ResultCode": "", "ResultText": "",
            "SourceFile": APPROVAL_PENDING + ".json",
        },
        {
            "Title": APPROVAL_APPROVED, "Repo": "luna", "Ticket": "RDSD-140", "ApprovalKind": "jira-create",
            "Summary": "Create Jira issue RDSD-140: nightly diff of the DPM extracts",
            "PayloadPreview": '{"project":"RDSD","issuetype":"Task","summary":"Nightly diff of the DPM extracts"}',
            "PayloadTruncated": "false", "PayloadBytes": "91", "Digest": DIGEST_C, "Created": "2026-09-25T16:03:01Z",
            "Expires": "2026-09-25T16:33:01Z", "WaitingSeconds": "219", "Status": "approved", "DecidedBy": OPERATOR,
            "DecidedAt": "2026-09-25T16:06:40Z", "Reason": "", "Via": "mobile", "Late": "false",
            "Nonce": NONCE_APPLIED, "ResultCode": "", "ResultText": "", "SourceFile": APPROVAL_APPROVED + ".json",
        },
        {
            "Title": APPROVAL_DENIED, "Repo": "dpm-reports", "Ticket": "DPM-77", "ApprovalKind": "pncli-write",
            "Summary": "Publish the DPM-77 report to the production workspace",
            "PayloadPreview": '{"truncated":true,"bytes":9120,"head":"{\\"workspace\\":\\"Production\\",\\"report\\":\\"DPM-77 weekly\\", ..."}',
            "PayloadTruncated": "true", "PayloadBytes": "9120", "Digest": DIGEST_D, "Created": "2026-09-25T11:00:00Z",
            "Expires": "2026-09-25T11:30:00Z", "WaitingSeconds": "61", "Status": "denied", "DecidedBy": "operator",
            "DecidedAt": "2026-09-25T11:01:01Z", "Reason": "Wrong workspace; retarget to UAT first.", "Via": "laptop",
            "Late": "false", "Nonce": "", "ResultCode": "", "ResultText": "", "SourceFile": APPROVAL_DENIED + ".json",
        },
    ],
    "FleetDecisions": [
        {
            "Title": NONCE_APPLIED, "Kind": "decision", "ApprovalId": APPROVAL_APPROVED, "Repo": "luna",
            "Decision": "approved", "Reason": "", "Message": "", "AnswersJson": "", "Digest": DIGEST_C, "By": OPERATOR,
            "Device": "ios-phone", "Issued": "2026-09-25T16:05:12Z", "Expires": "2026-09-25T16:20:12Z",
            "InboxFile": "decision-%s.json" % NONCE_APPLIED, "Result": "applied", "ResultCode": "", "ResultText": "",
            "ResultAt": "2026-09-25T16:06:40Z",
        },
        {
            "Title": NONCE_REPLY, "Kind": "reply", "ApprovalId": "", "Repo": "luna", "Decision": "", "Reason": "",
            "Message": "", "AnswersJson": '[{"id":"q1","answer":"calendar month"}]', "Digest": "", "By": OPERATOR,
            "Device": "android-phone", "Issued": "2026-09-26T09:20:31Z", "Expires": "2026-09-26T09:35:31Z",
            "InboxFile": "reply-%s.json" % NONCE_REPLY, "Result": "sent", "ResultCode": "", "ResultText": "",
            "ResultAt": "",
        },
        {
            "Title": NONCE_REJECTED, "Kind": "decision", "ApprovalId": APPROVAL_EXPIRED, "Repo": "rdsd-uat",
            "Decision": "approved", "Reason": "", "Message": "", "AnswersJson": "", "Digest": DIGEST_A, "By": OPERATOR,
            "Device": "ios-phone", "Issued": "2026-09-24T08:44:10Z", "Expires": "2026-09-24T08:59:10Z",
            "InboxFile": "decision-%s.json" % NONCE_REJECTED, "Result": "rejected", "ResultCode": "mobile_expired",
            "ResultText": "the decision expired before the laptop saw it decide again from the desk or the phone",
            "ResultAt": "2026-09-24T09:05:11Z",
        },
    ],
    "FleetNotifications": [
        {
            "Title": "luna:needs_human", "Repo": "luna", "Ticket": "RDSD-118", "State": "needs_human",
            "Severity": "action", "TitleText": "luna · RDSD-118 — needs you",
            "Body": "Two readings of the acceptance criteria lead to different work; asked which date window to use "
                    "and stopped.",
            "At": "2026-09-26T09:14:05Z", "Seq": "187", "Quiet": "false", "ApprovalId": "",
            "SourceFile": "20260926T091405Z-luna-needs_human-187.json",
        },
        {
            "Title": "rdsd-uat:waiting_approval", "Repo": "rdsd-uat", "Ticket": "RDSD-131", "State": "waiting_approval",
            "Severity": "action", "TitleText": "rdsd-uat · RDSD-131 — a write is waiting for one click",
            "Body": "a write is waiting for one click", "At": "2026-09-26T09:12:01Z", "Seq": "42", "Quiet": "false",
            "ApprovalId": APPROVAL_PENDING, "SourceFile": "20260926T091201Z-rdsd-uat-waiting_approval-42.json",
        },
        {
            "Title": "dpm-reports:done", "Repo": "dpm-reports", "Ticket": "DPM-77", "State": "done", "Severity": "info",
            "TitleText": "dpm-reports · DPM-77 — done", "Body": "phase is report",
            "At": "2026-09-25T23:40:12Z", "Seq": "880", "Quiet": "true", "ApprovalId": "",
            "SourceFile": "20260925T234012Z-dpm-reports-done-880.json",
        },
    ],
    # The live list holds exactly one row (Title = laptop; the flow upserts it). These three rows are the
    # same row at three successive heartbeats and exist only to seed the column types.
    "FleetHeartbeat": [
        {
            "Title": "laptop", "At": "2026-09-26T09:05:00Z", "EverySeconds": "300", "ExpireSeconds": "900",
            "Contract": "1", "Operator": OPERATOR, "Bridge": "agentdata 0.9.0", "LaptopId": LAPTOP_ID,
            "ServeUp": "true", "DeskStreams": "1", "Repos": "3", "NeedsHuman": "0", "ApprovalsPending": "0",
            "Notifications24h": "8", "Rejected24h": "0", "InboxLastSeen": "2026-09-26T09:04:58Z",
        },
        {
            "Title": "laptop", "At": "2026-09-26T09:10:00Z", "EverySeconds": "300", "ExpireSeconds": "900",
            "Contract": "1", "Operator": OPERATOR, "Bridge": "agentdata 0.9.0", "LaptopId": LAPTOP_ID,
            "ServeUp": "true", "DeskStreams": "2", "Repos": "3", "NeedsHuman": "0", "ApprovalsPending": "0",
            "Notifications24h": "8", "Rejected24h": "0", "InboxLastSeen": "2026-09-26T09:09:58Z",
        },
        {
            "Title": "laptop", "At": "2026-09-26T09:15:00Z", "EverySeconds": "300", "ExpireSeconds": "900",
            "Contract": "1", "Operator": OPERATOR, "Bridge": "agentdata 0.9.0", "LaptopId": LAPTOP_ID,
            "ServeUp": "true", "DeskStreams": "2", "Repos": "3", "NeedsHuman": "1", "ApprovalsPending": "1",
            "Notifications24h": "9", "Rejected24h": "0", "InboxLastSeen": "2026-09-26T09:14:58Z",
        },
    ],
}


def build(path: str) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    wb.properties.creator = "make_workbook.py"
    wb.properties.lastModifiedBy = "make_workbook.py"
    wb.properties.created = FIXED_DATE
    wb.properties.modified = FIXED_DATE
    for name, columns in COLUMNS.items():
        rows = ROWS[name]
        ws = wb.create_sheet(title=name)
        ws.append(columns)
        for row in rows:
            missing = set(columns) - set(row)
            extra = set(row) - set(columns)
            if missing or extra:
                raise SystemExit(f"{name}: row keys off by missing={sorted(missing)} extra={sorted(extra)}")
            values = [row[c] for c in columns]
            if not all(isinstance(v, str) for v in values):
                raise SystemExit(f"{name}: every cell must be text")
            ws.append(values)
        last = f"{get_column_letter(len(columns))}{len(rows) + 1}"
        table = Table(displayName=name, ref=f"A1:{last}")
        table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        ws.add_table(table)
        ws.freeze_panes = "A2"
        for i, c in enumerate(columns, start=1):
            longest = max([len(c)] + [len(r[c]) for r in rows])
            ws.column_dimensions[get_column_letter(i)].width = min(max(12, longest + 2), 48)
    wb.save(path)


def normalize_zip(src: str, dst: str) -> None:
    """Re-zip with pinned entry timestamps so the bytes do not depend on the clock.

    ``Workbook.save`` stamps ``dcterms:modified`` with the current time whatever the properties say, so that
    element is pinned here as well.
    """
    stamp = FIXED_DATE.strftime("%Y-%m-%dT%H:%M:%SZ").encode("ascii")
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "docProps/core.xml":
                data = re.sub(rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*(</dcterms:(?:created|modified)>)",
                              rb"\g<1>" + stamp + rb"\g<2>", data)
            out = zipfile.ZipInfo(info.filename, date_time=ZIP_DATE)
            out.compress_type = zipfile.ZIP_DEFLATED
            out.external_attr = info.external_attr
            zout.writestr(out, data)


def check(path: str) -> str:
    """Re-open the workbook and assert what the two consumers rely on. Returns a one-line summary."""
    wb = load_workbook(path)
    assert wb.sheetnames == list(COLUMNS), wb.sheetnames
    for name, columns in COLUMNS.items():
        ws = wb[name]
        assert name in ws.tables, f"{name}: table missing (have {list(ws.tables)})"
        expected_ref = f"A1:{get_column_letter(len(columns))}{len(ROWS[name]) + 1}"
        assert ws.tables[name].ref == expected_ref, (name, ws.tables[name].ref, expected_ref)
        header = [c.value for c in ws[1]]
        assert header == columns, (name, header)
        # An empty cell reads back as None; everything else must be the text that was written.
        for i, row in enumerate(ws.iter_rows(min_row=2, max_row=len(ROWS[name]) + 1)):
            got = [("" if cell.value is None else cell.value) for cell in row]
            assert all(isinstance(v, str) for v in got), (name, i, [type(v) for v in got])
            assert got == [ROWS[name][i][c] for c in columns], (name, i, got)
        assert ws.max_row == len(ROWS[name]) + 1, (name, ws.max_row)
        assert MULTILINE[name] <= set(columns), (name, MULTILINE[name] - set(columns))
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    tables = ", ".join(f"{n}({len(c)} cols, {len(ROWS[n])} rows)" for n, c in COLUMNS.items())
    return f"ok: {tables}; sha256 {digest[:16]}"


def main() -> int:
    tmpdir = tempfile.mkdtemp(prefix="fleetagent-xlsx-")
    try:
        raw = os.path.join(tmpdir, "raw.xlsx")
        build(raw)
        normalize_zip(raw, OUT)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"wrote {os.path.relpath(OUT)}")
    print("check", check(OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
