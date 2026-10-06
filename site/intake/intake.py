#!/usr/bin/env python3
"""The laptop's half of Intake -> Jira (site/intake/README.md). Stdlib only; it runs `ad-jira`, never imports it.

    python site/intake/intake.py list                    the intake rows the site sent that are not in Jira yet
    python site/intake/intake.py file <id> [--dry-run]   open each as a Jira ticket (ad-jira create: one approval each)
    python site/intake/intake.py file --all [--dry-run]
    python site/intake/intake.py sync                    read each open ticket's status and send it back to the row

`CzarsIntakeOut` (a flow) writes every new Intake row to `<folder>/intake/intake-<id>.json` in the operator's
OneDrive. This script turns one into a ticket with `ad-jira create`, which takes the project's facts from the
scanned context and waits for the operator's approval on the desk or the phone (the fleet's approval gate). It then
writes `<folder>/results/<id>-<time>.json`, which `CzarsIntakeBack` (the other flow) applies to the row: the Jira key,
the link, the status and a sentence. `<folder>/ledger.json` remembers which rows are filed, so nothing is filed twice.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONTEXT = os.path.join(ROOT, "site", "local", "context.json")
#: The intake type a person picks on the site, and the key of `jira.issueTypes` it files under.
TYPE_KEYS = {"Report an issue": "issue", "Request work": "request", "Ask a question": "question", "Request access": "access"}
#: Jira's status categories, and the Intake status each one shows on the site.
CATEGORY_STATUS = {"new": "Sent to Jira", "indeterminate": "In progress", "done": "Done"}
CLOSED = {"Done", "Declined"}
ENTITY = "SP.Data.IntakeListItem"


class Refused(Exception):
    pass


def default_folder() -> str:
    base = os.environ.get("OneDriveCommercial") or os.environ.get("OneDrive") or os.path.expanduser("~")
    return os.path.join(base, "DataCzars")


def load_context(path: str = CONTEXT) -> dict:
    if not os.path.exists(path):
        raise Refused(f"{path} does not exist: run the scans and `python site/provision.py context` first")
    with open(path, encoding="utf-8") as f:
        ctx = json.load(f)
    jira = ctx.get("jira", {})
    missing = [k for k in ("url", "project") if not jira.get(k)]
    if missing:
        raise Refused(f"the context has no jira.{', jira.'.join(missing)}: the data-czars scan fills them from AGENTS.md")
    return ctx


def _read(path: str) -> dict:
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def _write(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def ledger(folder: str) -> dict:
    path = os.path.join(folder, "ledger.json")
    return _read(path) if os.path.exists(path) else {}


def pending(folder: str) -> list[dict]:
    """Intake files with no ledger entry, oldest id first."""
    done = ledger(folder)
    out = []
    inbox = os.path.join(folder, "intake")
    for name in sorted(os.listdir(inbox)) if os.path.isdir(inbox) else []:
        m = re.fullmatch(r"intake-(\d+)\.json", name)
        if m and m.group(1) not in done:
            out.append(_read(os.path.join(inbox, name)))
    return sorted(out, key=lambda row: int(row["id"]))


def ticket(row: dict, ctx: dict) -> dict:
    """What `ad-jira create` is given for one intake row: summary, description, type, components, labels."""
    jira = ctx["jira"]
    kind = row.get("type") or "Report an issue"
    issue_type = (jira.get("issueTypes") or {}).get(TYPE_KEYS.get(kind, "issue")) or "Task"
    product = row.get("product") or ""
    component = next((p.get("jiraComponent") for p in ctx.get("products", [])
                      if p.get("name") == product and p.get("jiraComponent")), "")
    lines = [row.get("details", "").strip(), "", f"Type: {kind}"]
    for label, key in (("Product", "product"), ("How much it hurts", "impact"), ("Who is affected", "affectedTeam"),
                       ("Needed by", "neededBy")):
        if row.get(key):
            lines.append(f"{label}: {row[key]}")
    who = row.get("requesterName") or row.get("requester") or "someone"
    if row.get("requester") and row.get("requesterName"):
        who = f"{row['requesterName']} <{row['requester']}>"
    lines.append(f"Raised by {who} on the Data Czars site, intake #{row['id']}.")
    if row.get("link"):
        lines.append(f"Intake row: {row['link']}")
    prefix = {"Report an issue": "Issue", "Request work": "Request", "Ask a question": "Question",
              "Request access": "Access"}.get(kind, "Intake")
    summary = f"{prefix}{f' ({product})' if product else ''}: {row.get('title', '').strip()}"
    return {"summary": summary[:250], "description": "\n".join(lines).strip() + "\n", "type": issue_type,
            "project": jira["project"], "components": [component] if component else [],
            "labels": list(jira.get("labels") or [])}


def create_args(t: dict, description_file: str, dry_run: bool) -> list[str]:
    args = ["ad-jira", "create", "--summary", t["summary"], "--description-file", description_file,
            "--project", t["project"], "--type", t["type"]]
    for c in t["components"]:
        args += ["--component", c]
    for label in t["labels"]:
        args += ["--label", label]
    if dry_run:
        args.append("--dry-run")
    return args


def run(args: list[str]) -> tuple[int, str]:
    """Run an ad-* command and return its exit code and output. Tests replace this."""
    try:
        done = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise Refused(f"{args[0]} is not installed here: this runs on the laptop with the this-next-please CLI")
    return done.returncode, (done.stdout or "") + (done.stderr or "")


def key_in(output: str, project: str) -> str:
    m = re.search(rf"\b{re.escape(project)}-\d+\b", output)
    return m.group(0) if m else ""


def meta_value(output: str, name: str) -> str:
    m = re.search(rf"^\s*{re.escape(name)}:\s*\"?(.*?)\"?\s*$", output, re.M)
    return m.group(1) if m else ""


def result(row_id: str, fields: dict) -> dict:
    """The file CzarsIntakeBack applies: the row's id and the fields to merge into it."""
    return {"id": int(row_id), "merge": dict({"__metadata": {"type": ENTITY}}, **fields)}


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _stamp(now: dt.datetime) -> str:
    return now.strftime("%Y%m%dT%H%M%SZ")


def file_rows(folder: str, ctx: dict, ids: list[str] | None, dry_run: bool) -> list[str]:
    report = []
    rows = pending(folder)
    if ids:
        rows = [r for r in rows if str(r["id"]) in ids]
        missing = set(ids) - {str(r["id"]) for r in rows}
        report += [f"#{i}: no pending intake file (already filed, or not synced yet)" for i in sorted(missing)]
    book = ledger(folder)
    for row in rows:
        t = ticket(row, ctx)
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(t["description"])
            description_file = f.name
        try:
            code, output = run(create_args(t, description_file, dry_run))
        finally:
            os.unlink(description_file)
        if dry_run:
            report.append(f"#{row['id']}: would file {t['type']} in {t['project']}: {t['summary']}")
            continue
        key = key_in(output, t["project"])
        if code != 0 or not key:
            report.append(f"#{row['id']}: not filed (ad-jira said: {output.strip().splitlines()[-1] if output.strip() else code})")
            continue
        now = _now()
        url = f"{ctx['jira']['url'].rstrip('/')}/browse/{key}"
        _write(os.path.join(folder, "results", f"{row['id']}-{_stamp(now)}.json"), result(str(row["id"]), {
            "JiraKey": key, "JiraLink": {"__metadata": {"type": "SP.FieldUrlValue"}, "Url": url, "Description": key},
            "Status": "Sent to Jira", "SyncNote": f"Filed as {key} on {now:%Y-%m-%d}."}))
        book[str(row["id"])] = {"key": key, "status": "Sent to Jira", "at": now.isoformat(timespec="seconds")}
        _write(os.path.join(folder, "ledger.json"), book)
        report.append(f"#{row['id']}: {key}")
    return report


def sync(folder: str, ctx: dict) -> list[str]:
    report = []
    book = ledger(folder)
    for row_id, entry in sorted(book.items(), key=lambda kv: int(kv[0])):
        if entry.get("status") in CLOSED:
            continue
        code, output = run(["ad-jira", "transitions", entry["key"]])
        category = meta_value(output, "status_category").lower()
        jira_status = meta_value(output, "status")
        status = CATEGORY_STATUS.get(category)
        if code != 0 or not status:
            report.append(f"#{row_id} {entry['key']}: status not read")
            continue
        if status == entry.get("status") and jira_status == entry.get("jiraStatus"):
            continue
        now = _now()
        _write(os.path.join(folder, "results", f"{row_id}-{_stamp(now)}.json"), result(row_id, {
            "Status": status, "SyncNote": f"Jira says {jira_status} ({now:%Y-%m-%d})."}))
        entry.update(status=status, jiraStatus=jira_status, at=now.isoformat(timespec="seconds"))
        report.append(f"#{row_id} {entry['key']}: {jira_status}")
    _write(os.path.join(folder, "ledger.json"), book)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="intake.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--folder", default=default_folder(), help="the OneDrive folder the intake flows use")
    parser.add_argument("--context", default=CONTEXT)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("file")
    p.add_argument("ids", nargs="*")
    p.add_argument("--all", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    sub.add_parser("sync")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "list":
            rows = pending(args.folder)
            for row in rows:
                print(f"#{row['id']}  {row.get('type', '')}  {row.get('product') or '-'}  {row.get('title', '')}")
            print(f"{len(rows)} waiting")
            return 0
        ctx = load_context(args.context)
        if args.cmd == "file":
            if not args.ids and not args.all:
                parser.error("name the intake ids, or --all")
            lines = file_rows(args.folder, ctx, None if args.all else args.ids, args.dry_run)
        else:
            lines = sync(args.folder, ctx)
        print("\n".join(lines) if lines else "nothing to do")
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
