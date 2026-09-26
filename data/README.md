# FleetAgent list-provisioning workbook

`FleetAgent.xlsx` holds five Excel tables named after the five lists of the mobile contract (v1):
`FleetAttention`, `FleetApprovals`, `FleetDecisions`, `FleetNotifications`, `FleetHeartbeat`. Each table's
header row is the contract's columns in order and each carries three sample rows. It is generated, never edited
by hand:

```
python -m pip install --user openpyxl     # once; not a project dependency
python mobile/data/make_workbook.py       # rewrites FleetAgent.xlsx and re-checks it
```

The script is deterministic (fixed dates, no random values, pinned document properties and zip timestamps), so a
re-run produces identical bytes and the committed file never churns. Its last step re-opens the workbook and
asserts the five tables, their references and their headers.

Two uses:

1. **Microsoft Lists > Create a list > From Excel** builds each list with the right columns (below).
2. The same workbook is the **Excel Online (Business) fallback store** when the operator has no SharePoint site
   to put lists on (further below).

## Creating the five lists from the workbook

Repeat once per table (five times), in Microsoft Lists (or the SharePoint site's **New > List**):

1. **Create a list > From Excel > Upload file** (`FleetAgent.xlsx`). Under *Select a table from this file*
   pick the table with the list's name (`FleetAttention` first).
2. Set the column types in the preview: **Single line of text** for every column, except the multi-line ones
   in the table below, which get **Multiple lines of text**. Columns whose samples look numeric (`AgeSeconds`,
   `Seq`, `SpendTotal` ...) are offered as *Number*: change them to *Single line of text*; every column is text
   in this contract (numbers and booleans travel as text, so the app and the flows never fight Excel or
   SharePoint type coercion). `At`/`Issued`/`Expires` stay text too, never *Date and time*.
3. The first column, `Title`, becomes the list's Title column (the list's key: repo alias, approval id, nonce,
   notification key, or `laptop`). If the dialog maps it to a separate text column instead, delete that column
   after creation and keep SharePoint's own `Title` (the flows write `Title` by that internal name).
4. Name = the table's name, exactly (`FleetAttention` ...). The flows and the app address lists by these names.
5. **Create**. Then, for every *Multiple lines of text* column: column header > **Column settings > Edit** >
   *More options* > **Use enhanced rich text** = No (plain text; the columns hold JSON and prose, and rich text
   would wrap them in HTML).
6. **Delete the three sample rows.** They exist to fix the column types and to show a reader what a row looks
   like; a live list must not start with `luna`, `rdsd-uat` or `dpm-reports` in it, and `FleetHeartbeat` holds
   exactly one row (`laptop`), upserted by the flow.

Import can create the column order differently from the table; order does not matter to the flows or the app
(both address columns by name). What matters is the internal name: create the columns with these names on the
first try, because SharePoint freezes the internal name at creation and a later rename only changes the display
name (a column created as `Needs human` and renamed `NeedsHuman` has the internal name `Needs_x0020_human`, and
`Title eq` style filters and `item/NeedsHuman` writes would miss it).

## Columns per list

Type: *text* = Single line of text (255 characters maximum), *multi* = Multiple lines of text (plain). "Max"
is the contract's longest value; the flow truncates the three single-line columns that can legally exceed 255
(`Summary`, `Reason`, `ResultText`) and writes every other column whole.

### `FleetAttention` (Title = repo alias; one row per repo, upserted; source file `attention/<repo>-<seq>.json`)

| Column | Type | Max | JSON field | Notes |
|---|---|---|---|---|
| `Title` | text | 64 | `repo` | registry name of the repo |
| `Project` | text | 64 | `project` | |
| `Ticket` | text | 32 | `ticket` | `RDSD-118` shape or empty |
| `State` | text | 16 | `state` | `starting, running, waiting_approval, needs_human, blocked, idle, done, error` |
| `Role` | text | 8 | `role` | `running, waiting, human, done, idle` |
| `NeedsHuman` | text | 5 | `needs_human` | `true`/`false` |
| `Says` | **multi** | 300 | `says` | scrubbed prose |
| `LastSaid` | text | 200 | `last_said` | |
| `AgeSeconds` | text | 10 | `age_s` | |
| `At` | text | 20 | `at` | `YYYY-MM-DDTHH:MM:SSZ` |
| `Generated` | text | 20 | `generated` | |
| `ApprovalId` | text | 96 | `approval_id` | oldest pending approval or empty |
| `ApprovalsJson` | text | 800 | `approvals` | JSON array of ids (up to 8 x 96); over 255 only when many approvals pile up, see flows README "Verify on import" row 19 |
| `QuestionsJson` | **multi** | 5000 | `questions` | JSON array of `{id, q, choices, want, default}` |
| `RunNumber` | text | 6 | `run.n` | |
| `RunOrigin` | text | 8 | `run.origin` | `console, adopted, fleet` |
| `RunLive` | text | 5 | `run.live` | |
| `Model` | text | 64 | `model` | |
| `SpendLine` | text | 64 | `spend.line` | `4.3 premium · of 10 · 12 turns` |
| `SpendTotal` | text | 16 | `spend.total` | |
| `SpendToday` | text | 16 | `spend.today` | |
| `SpendBudget` | text | 16 | `spend.budget` | empty when no budget |
| `Turns` | text | 6 | `spend.turns` | |
| `Supervised` | text | 5 | `supervised` | |
| `External` | text | 5 | `external` | "somebody else's session": the app disables reply |
| `Digest` | text | 64 | `digest` | sha256 hex, change detection only |
| `Seq` | text | 10 | `seq` | file sequence; the flow only updates when the file's `seq` is not older than the row's |

### `FleetApprovals` (Title = approval id; source files `approvals/<id>.json`, `approvals/<id>.decision.json`, `results/<nonce>.result.json`)

| Column | Type | Max | JSON field | Notes |
|---|---|---|---|---|
| `Title` | text | 96 | `id` | `<repo>-<kind>-<stamp>-<hex>` |
| `Repo` | text | 64 | `repo` | |
| `Ticket` | text | 32 | `ticket` | |
| `ApprovalKind` | text | 32 | `approval_kind` | `jira-transition, jira-create, pncli-write` |
| `Summary` | text | 300 -> 255 | `summary` | truncated by the flow |
| `PayloadPreview` | **multi** | 8192 | `payload_preview` | JSON text of the dry-run payload, or `{"truncated":true,"bytes":N,"head":"..."}` |
| `PayloadTruncated` | text | 5 | `payload_truncated` | |
| `PayloadBytes` | text | 10 | `payload_bytes` | |
| `Digest` | text | 64 | `digest` | the app echoes it in `FleetDecide`; the laptop verifies it |
| `Created` | text | 20 | `created` | |
| `Expires` | text | 20 | `expires` | the agent's own deadline |
| `WaitingSeconds` | text | 10 | `waiting_s` | at export |
| `Status` | text | 8 | (flow) | `pending, sent, approved, denied, rejected, expired` |
| `DecidedBy` | text | 254 | `by` | UPN (mobile) or the laptop user |
| `DecidedAt` | text | 20 | `decided` | |
| `Reason` | text | 500 -> 255 | `reason` | truncated by the flow |
| `Via` | text | 6 | `via` | `laptop, mobile` |
| `Late` | text | 5 | `late` | empty until decided |
| `Nonce` | text | 64 | `nonce` | present when decided from the phone |
| `ResultCode` | text | 32 | result `code` | filled when the laptop rejected the phone's decision |
| `ResultText` | text | 255 | result `error` + `hint` | truncated by the flow |
| `SourceFile` | text | 120 | (trigger) | name of the outbox file that created the row |

### `FleetDecisions` (Title = nonce; created by `FleetDecide`, updated from `results/<nonce>.result.json`)

| Column | Type | Max | Source | Notes |
|---|---|---|---|---|
| `Title` | text | 64 | nonce | 32 lowercase hex from `replace(guid(), '-', '')` |
| `Kind` | text | 8 | app `Kind` | `decision, reply` |
| `ApprovalId` | text | 96 | app `ApprovalId` | decisions only |
| `Repo` | text | 64 | app `Repo` | replies only |
| `Decision` | text | 8 | app `Decision` | `approved, denied` |
| `Reason` | text | 500 -> 255 | app `Reason` | truncated in the row, whole in the inbox file |
| `Message` | **multi** | 4000 | app `Message` | |
| `AnswersJson` | **multi** | 9000 | app `AnswersJson` | JSON array of `{id, answer}` |
| `Digest` | text | 64 | app `Digest` | |
| `By` | text | 254 | Get my profile (V2) | the invoker's UPN, never app-supplied |
| `Device` | text | 64 | app `Device` | informational |
| `Issued` | text | 20 | flow | |
| `Expires` | text | 20 | flow | `Issued + ExpiresSeconds` |
| `InboxFile` | text | 80 | flow | `decision-<nonce>.json` / `reply-<nonce>.json` |
| `Result` | text | 8 | flows | `sent` (FleetDecide), then `applied` or `rejected` (FleetOutboxToLists) |
| `ResultCode` | text | 32 | result file | `mobile_expired, mobile_digest_mismatch, ...` |
| `ResultText` | text | 255 | result file | `error` + `hint` |
| `ResultAt` | text | 20 | result file | |

### `FleetNotifications` (Title = key; source `notifications/<at>-<repo>-<state>-<seq>.json`)

| Column | Type | Max | JSON field | Notes |
|---|---|---|---|---|
| `Title` | text | 81 | `key` | `<repo>:<state>`; a newer `seq` for the same key updates the row |
| `Repo` | text | 64 | `repo` | |
| `Ticket` | text | 32 | `ticket` | |
| `State` | text | 16 | `state` | |
| `Severity` | text | 6 | `severity` | `action, alert, info`; the flow's own failure rows use `alert` |
| `TitleText` | text | 120 | `title` | `<repo> · <ticket> — <phrase>` |
| `Body` | **multi** | 300 | `body` | scrubbed |
| `At` | text | 20 | `at` | |
| `Seq` | text | 10 | `seq` | |
| `Quiet` | text | 5 | `quiet` | quiet hours: row written, no push |
| `ApprovalId` | text | 96 | `approval_id` | |
| `SourceFile` | text | 120 | (trigger) | |

### `FleetHeartbeat` (Title = `laptop`; exactly one row; source `heartbeat/<yyyymmdd-hhmm>.json` every 300 s)

| Column | Type | Max | JSON field | Notes |
|---|---|---|---|---|
| `Title` | text | 6 | (constant) | `laptop` |
| `At` | text | 20 | `at` | the phone's "laptop not syncing" rule: `now - At > 3 x EverySeconds` |
| `EverySeconds` | text | 6 | `every_s` | 300 |
| `ExpireSeconds` | text | 6 | `expire_s` | what the app passes to `FleetDecide` as `ExpiresSeconds` |
| `Contract` | text | 4 | `contract` | 1 |
| `Operator` | text | 254 | `operator` | the UPN the laptop accepts in `by` |
| `Bridge` | text | 64 | `bridge` | the laptop's version string |
| `LaptopId` | text | 64 | `laptop_id` | random hex, never the hostname |
| `ServeUp` | text | 5 | `serve_up` | |
| `DeskStreams` | text | 6 | `desk_streams` | |
| `Repos` | text | 6 | `counts.repos` | |
| `NeedsHuman` | text | 6 | `counts.needs_human` | |
| `ApprovalsPending` | text | 6 | `counts.approvals_pending` | |
| `Notifications24h` | text | 6 | `counts.notifications_24h` | |
| `Rejected24h` | text | 6 | `counts.rejected_24h` | |
| `InboxLastSeen` | text | 20 | `inbox_last_seen` | |

## The Excel Online (Business) fallback

When there is no SharePoint site, the same workbook (with the sample rows deleted) is the store, through the
Excel Online (Business) connector (Standard, unblockable). Facts from the connector reference, and what each one
means here (research Q3):

| Fact | Consequence |
|---|---|
| "Users should avoid writing data to a single Excel file from multiple clients concurrently" (one writer per workbook) | **two copies**: `FleetAgent.xlsx` is written only by `FleetOutboxToLists`; a copy `FleetAgent-Decisions.xlsx` (same tables) is written only by `FleetDecide`. `FleetDecide` therefore skips its "mark the approval `sent`" step in this variant (the `FleetDecisions` row already says `sent`), and `FleetOutboxToLists` writes its `result` updates to the `FleetDecisions` table of `FleetAgent-Decisions.xlsx` (the table the app reads), so that one table has two flow writers at low volume, both as upserts with Concurrency control = 1; its `decision` updates go to `FleetApprovals` in `FleetAgent.xlsx`. The app reads `FleetDecisions` from the Decisions workbook and the other four tables from `FleetAgent.xlsx`: one data source per table name, so no formula changes. F6 proves this once or drops the Excel path. |
| A file may be locked for an update or delete for up to **6 minutes** after the last use of the connector; changes take up to **30 seconds** to be visible; filtered/sorted reads "may not be up to date" | set **Concurrency control = On, degree of parallelism 1** on the `FleetOutboxToLists` trigger (parallel Split On runs would fight over the lock; the setting is irreversible once enabled); expect the app to lag a heartbeat |
| Recalculation timeouts plus the retry policy insert rows multiple times | Retry Policy = None on every Add a row / Update a row, exactly as for SharePoint |
| **25 MB** maximum workbook size; **5 MB** per request; **100 calls per connection per 60 seconds** | prune: the laptop already caps notifications at 24 h and decided approvals at 24 h; delete old `FleetNotifications` rows from the workbook monthly |
| **List rows present in a table** returns 256 rows by default; `$filter` supports only `eq, ne, contains, startswith, endswith`, one filter per column, on a key column | every flow lookup is `Title eq '<key>'` on one column, which fits; turn on Pagination if a table ever passes 256 rows |
| Key Column name is case-sensitive; several key matches update only the first row | the key column is `Title` in every table; rows are unique by `Title` by construction |
| `__PowerAppsId__`: Power Apps adds a hidden column of that name to a table it connects to, to give rows an identity (up to 64,000 rows auto-populated when *Insert auto generated id into Excel table* is chosen) | let it; the flows never write it and the column list above is unchanged for them; do not delete it |
| The connector has **no automated row trigger** (only the instant *For a selected row*) | nothing is lost: the app never relies on a row-added trigger, it calls `FleetDecide` directly, and `FleetOutboxToLists` is triggered by OneDrive files, not by rows |
| A read-only action can still create a new file version | ignore version history noise on the workbook |

Action mapping for the fallback: SharePoint **Get items** (`Title eq '<key>'`, Top 1) -> Excel **List rows
present in a table** (Location / Document Library / File / Table, Filter Query `Title eq '<key>'`, Top Count 1);
**Create item** -> **Add a row into a table**; **Update item** (by Id) -> **Update a row** (Key Column `Title`,
Key Value the key; "columns left blank will not be updated", so pass every column). Everything else in the flows
(expressions, conditions, pushes) is unchanged.

## The sample rows

Three rows per table, all fictional: repo aliases `luna`, `rdsd-uat`, `dpm-reports`; tickets `RDSD-118`,
`RDSD-131`, `RDSD-140`, `DPM-77`; the operator is always `operator@example.com`; digests, nonces and the laptop id
are arbitrary hex. No hostname, path, token or real name appears anywhere in the workbook (the same allow-list
rule the laptop's exporter follows). They show, per list, the states the app must render: an agent that needs a
human with an open question, one waiting for an approval, one running unsupervised; a pending, an approved
(via mobile, with its nonce) and a denied (via laptop) approval; an applied decision, a sent reply and a rejected
decision (`mobile_expired`); an action notification, one carrying an approval id, and a quiet info one; and the
heartbeat row at three successive beats. The values agree with `../flows/samples/*.json`, which are the outbox
files that would have produced them, so a reviewer can follow one record from file to row. Delete them from any
live list or workbook before use.
