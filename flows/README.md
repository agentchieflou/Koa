# FleetAgent mobile lane: the two Power Automate flows

Two cloud flows connect the laptop's OneDrive bridge (`ad-fleet`'s outbox/inbox folders under the synced
`FleetAgent/` tree) to the five SharePoint lists the FleetAgent canvas app reads, and back:

| Flow | Kind | Trigger | Does |
|---|---|---|---|
| `FleetOutboxToLists` | automated | OneDrive for Business **When a file is created (properties only)** on `FleetAgent/outbox` (subfolders included) | one run per new `*.json`: Parse JSON, Switch on `kind`, upsert the matching list row by `Title`, push for approvals and non-info notifications |
| `FleetDecide` | instant | **Power Apps (V2)**, called by the app as `FleetDecide.Run(...)` | validates, writes `FleetAgent/inbox/<kind>-<nonce>.json` signed with the invoker's UPN, records the `FleetDecisions` row, marks the approval `sent`, responds `ok/nonce/inboxFile/error` |

Files here:

| File | What it is |
|---|---|
| `FleetOutboxToLists.definition.json`, `FleetDecide.definition.json` | the two flows in the shape of a solution's `Workflows/<name>-<guid>.json` (`properties.connectionReferences` + `properties.definition`). **The reviewable record.** Every place whose wire shape could not be verified against a Microsoft page carries a `_comment_unverified` sibling key and a row in [Verify on import](#verify-on-import). |
| `samples/*.json` | one outbox record per `kind` (contract v1), for **Use sample payload to generate schema** and for the test plan |
| `solution/` (not yet present) | where the operator checks in the exported unmanaged solution zip once a built flow works (see [Import sheet](#import-sheet)) |
| `../data/` | the list-provisioning workbook and its README (columns, types, Excel fallback) |

**The reliable path is the build sheet below, clicked in the designer.** The JSON is what a reviewer diffs and
what the operator compares against the export; a solution zip authored from scratch is undocumented (research
Q9), so nobody should try to import these two files directly.

Ground truth for every name in this document: `research_notes/Mobile fleet scope/flows_and_onedrive_bridge.md`
(connector reference names, operation IDs, limits), `laptop_bridge_design.md` Q2/Q4 (record formats) and
`notifications_intune_powerapps.md` KQ2/KQ3 (push and deep-link facts).

## Contract v1 in one screen

Timestamps are UTC text `YYYY-MM-DDTHH:MM:SSZ`; booleans are the text `true`/`false`; numbers are text; every
list column is text. JSON field names are snake_case, list columns are PascalCase of the same words, lists and
objects land in `*Json` columns as JSON text. The outbox files are immutable and uniquely named, so a *created*
trigger sees every one of them exactly once (plus the platform's at-least-once replays, which the upserts absorb).

| Outbox file | `kind` | Target list | Row key (`Title`) | Push |
|---|---|---|---|---|
| `attention/<repo>-<seq>.json` | `attention` | `FleetAttention` | repo alias | no |
| `approvals/<id>.json` | `approval` | `FleetApprovals` | approval id | yes: "An agent is waiting for your approval", `{"screen":"approval","approvalId":"<id>"}` |
| `approvals/<id>.decision.json` | `decision` | `FleetApprovals` (+ `FleetDecisions` when a nonce is present) | approval id / nonce | no |
| `notifications/<at>-<repo>-<state>-<seq>.json` | `notification` | `FleetNotifications` | key (`<repo>:<state>`) | when `quiet` is false and `severity` is not `info`: "Fleet: an agent needs you", `{"screen":"agent","repo":"<repo>"}` |
| `heartbeat/<yyyymmdd-hhmm>.json` | `heartbeat` | `FleetHeartbeat` | `laptop` | no |
| `results/<nonce>.result.json` | `result` | `FleetDecisions` (+ `FleetApprovals` when a decision was rejected) | nonce | no |

Inbox files the app causes to be written (by `FleetDecide`, never by the app directly):

| Inbox file | Fields |
|---|---|
| `decision-<nonce>.json` | `schema` (1), `kind` (`decision`), `nonce`, `issued`, `expires`, `by` (UPN), `id`, `digest`, `decision` (`approved`/`denied`), `reason`, `device` |
| `reply-<nonce>.json` | `schema`, `kind` (`reply`), `nonce`, `issued`, `expires`, `by`, `repo`, `message`, `answers` (`[{id, answer}]`), `device` |

`nonce` is `replace(guid(), '-', '')`: 32 lowercase hex characters, inside the laptop's `[A-Za-z0-9_-]{16,64}`
rule. Push messages are content-free on purpose: the OS shows the message text on the lock screen and Power Apps
mobile does not honour Intune's *Org data notifications* redaction (KQ2); everything specific rides in
`Parameters`, which the app reads with `Param("screen")` / `Param("approvalId")` / `Param("repo")` after unlock.

## Environment variables

Solution environment variables (Data type **Text**), referenced from the flows as
`@parameters('fleet_FleetSiteUrl (fleet_FleetSiteUrl)')`. **`fleet_` is the customization prefix of the solution
publisher** the operator creates (display name FleetAgent, prefix `fleet`). A different prefix means a
search-and-replace of `fleet_` in both definition files, which is the Microsoft-documented edit-the-JSON-and-rezip
step (Q9). Leave the *current value* empty before export so import prompts for it.

| Name (schema name) | Used by | Value | Where it comes from |
|---|---|---|---|
| `fleet_FleetSiteUrl` | both flows, every SharePoint action (Site Address) | `https://contoso.sharepoint.com/sites/FleetAgent` | the site that holds the five lists |
| `fleet_FleetOutboxFolderId` | `FleetOutboxToLists` trigger (Folder) | an opaque folder ID | pick `FleetAgent/outbox` once in the trigger's folder picker, read the stored `folderId` in the trigger's Code view, paste it here. It is tenant- and drive-specific. |
| `fleet_FleetInboxFolderPath` | `FleetDecide` Create file (Folder Path) | `/FleetAgent/inbox` | the path form; the operator's OneDrive |
| `fleet_FleetAppId` | `FleetOutboxToLists` push actions (Your app) | the canvas app GUID | Power Apps > Apps > FleetAgent > Details > App ID |
| `fleet_FleetOperatorEmail` | `FleetOutboxToLists` push actions (Recipients) | the operator's UPN | one user per push action (connector rule); the same UPN the laptop's `pairing.json` names as `operator` |

Changed values take effect only after the flow is saved or turned off and on again (Q9).

## Connections and connection references

All five connectors are Standard, Microsoft 365 seeded, and on the "cannot be blocked" DLP list (Q10, Q11).

| Connector | `apiId` | Connection reference (logical name) | Flow, actions | Run-only setting |
|---|---|---|---|---|
| OneDrive for Business | `/providers/Microsoft.PowerApps/apis/shared_onedriveforbusiness` | `fleet_sharedonedriveforbusiness_fleetagent` | `FleetOutboxToLists`: trigger, Get file content. `FleetDecide`: Create file | owner's connection (the operator owns both flows and the synced OneDrive) |
| SharePoint | `.../shared_sharepointonline` | `fleet_sharedsharepointonline_fleetagent` | every Get items / Create item / Update item | owner's connection |
| Power Apps Notification V2 | `.../shared_powerappsnotificationv2` | `fleet_sharedpowerappsnotificationv2_fleetagent` | `FleetOutboxToLists`: the two Send push notification V2 actions | owner's connection |
| Office 365 Users | `.../shared_office365users` | `fleet_sharedoffice365users_fleetagent` | `FleetDecide`: Get my profile (V2) | **Provided by run-only user**, so the profile is the invoker's (server-attested `by`) |
| Excel Online (Business) | `.../shared_excelonlinebusiness` | (fallback only) | replaces the SharePoint actions in the Excel fallback (`../data/README.md`) | owner's connection |

Throttles: OneDrive 100 calls/connection/minute, SharePoint 600, Excel 100 (Q1, Q3).

## Build sheet: `FleetOutboxToLists`

Create it inside the solution (**Solutions > FleetAgent > New > Automation > Cloud flow > Automated**). Names in
bold are the exact designer names to type when renaming each step (the JSON keys are the same names with spaces
replaced by underscores). Expressions are entered through **Add dynamic content > Expression** (or `fx`).

Notation used below: `J(x)` means `body('Parse_JSON')?['x']`; `J(a.b)` means `body('Parse_JSON')?['a']?['b']`.

### Trigger: **When a file is created (properties only)** (OneDrive for Business, `OnNewFilesV2`)

| Parameter | Value |
|---|---|
| Folder | pick `FleetAgent/outbox` (then move the stored ID into `fleet_FleetOutboxFolderId` and reference the variable, or leave the picked value: both work) |
| Include subfolders | Yes |
| Number of files to return | 20 |
| Settings > Split On | On (the default; one run per file) |
| Settings > Trigger conditions | `@endswith(triggerOutputs()?['body/Name'], '.json')` |
| Settings > Concurrency control | leave Off for SharePoint lists; set On, degree 1 for the Excel fallback (irreversible once enabled) |

The poll interval is the licence's: 5 minutes on Microsoft 365 plans, whatever the recurrence says (Q1).

### 1. **Try** (Control > Scope), containing steps 2-4

### 2. **Get file content** (OneDrive for Business, `GetFileContent`)

| Parameter | Value |
|---|---|
| File | `@triggerOutputs()?['body/Id']` |
| Infer Content Type | No |

### 3. **Parse JSON** (Data Operation)

| Parameter | Value |
|---|---|
| Content | `@json(base64ToString(body('Get_file_content')?['$content']))` |
| Schema | paste `properties.definition.actions.Try.actions.Parse_JSON.inputs.schema` from the definition file. Or **Use sample payload to generate schema** with the six `samples/*.json` merged into one object, then make every property except `kind` nullable (`"type": ["string","null"]` etc.), because each kind only carries its own fields. |

### 4. **Switch on kind** (Control > Switch), On = `@body('Parse_JSON')?['kind']`, six cases, empty Default

Every SharePoint action below: Site Address = `fleet_FleetSiteUrl`, List Name = the list named, and on every
**Create item** / **Update item**: **Settings > Networking > Retry Policy = None** (idempotency by `Title` comes
first; a retried insert is a duplicate). Get items: **Filter Query** as given, **Top Count** 1. Update item's
**Id** = `@first(outputs('<the Get items step>')?['body/value'])?['ID']`.

Column values follow four shapes, the same in every case:

| Column kind | Expression |
|---|---|
| text | `@coalesce(J(field), '')` |
| number | `@string(coalesce(J(field), ''))` |
| boolean | `@if(equals(J(field), true), 'true', 'false')` (not `string(true)`, which may render as `True`) |
| list/object into a `*Json` column | `@string(coalesce(J(field), json('[]')))` |
| single-line column that can exceed 255 (`Summary`, `Reason`, `ResultText`) | `@substring(v, 0, min(255, length(v)))` with `v = coalesce(J(field), '')` |

#### Case `attention`

1. **Get items FleetAttention**: Filter Query `Title eq '@{J(repo)}'`.
2. **Attention row exists** (Condition): `length(outputs('Get_items_FleetAttention')?['body/value'])` is greater than 0.
   - Yes: **Attention file is newer** (Condition): `int(coalesce(J(seq), 0))` is greater than or equal to the
     row's `Seq` (`int(if(empty(coalesce(first(...)?['Seq'], '')), '0', coalesce(first(...)?['Seq'], '')))`).
     Yes: **Update item FleetAttention**. No: nothing (an older file replayed after a newer one).
   - No: **Create item FleetAttention**.

Both write every column: `Title`=repo, `Project`, `Ticket`, `State`, `Role`, `NeedsHuman` (bool), `Says`,
`LastSaid`, `AgeSeconds` (age_s), `At`, `Generated`, `ApprovalId` (approval_id), `ApprovalsJson` (approvals),
`QuestionsJson` (questions), `RunNumber` (run.n), `RunOrigin` (run.origin), `RunLive` (run.live, bool), `Model`,
`SpendLine` (spend.line), `SpendTotal`, `SpendToday`, `SpendBudget`, `Turns` (spend.turns), `Supervised` (bool),
`External` (bool), `Digest`, `Seq`.

#### Case `approval`

1. **Get items FleetApprovals by id**: `Title eq '@{J(id)}'`.
2. **Approval row is new** (Condition): the length equals 0.
   - Yes: **Create item FleetApprovals** with `Title`=id, `Repo`, `Ticket`, `ApprovalKind` (approval_kind),
     `Summary` (truncated 255), `PayloadPreview` = `@string(coalesce(J(payload_preview), ''))` (object or text),
     `PayloadTruncated` (bool), `PayloadBytes`, `Digest`, `Created`, `Expires`, `WaitingSeconds` (waiting_s),
     `Status` = `pending`, `SourceFile` = `@triggerOutputs()?['body/Name']`, and `DecidedBy`, `DecidedAt`,
     `Reason`, `Via`, `Late`, `Nonce`, `ResultCode`, `ResultText` empty. Then **Send push notification V2
     approval** (Power Apps Notification V2): Mobile app = Power Apps, Your app = `fleet_FleetAppId`, Recipients
     Item-1 = `fleet_FleetOperatorEmail`, Message = `An agent is waiting for your approval`, Open app = Yes,
     Parameters = `{"screen":"approval","approvalId":"@{J(id)}"}`.
   - No (replay, or the decision mirror got there first): **Approval row has no summary** (Condition):
     `empty(coalesce(first(...)?['Summary'], ''))` is equal to `true`. Yes: **Update item FleetApprovals
     descriptive** with the descriptive columns only (never `Status`). No: nothing.

#### Case `decision`

1. **Get items FleetApprovals for decision**: `Title eq '@{J(id)}'`.
2. **Approval row found for decision** (Condition): length greater than 0.
   - Yes: **Update item FleetApprovals decided**: `Title`=id, `Status` = decision, `DecidedBy` = by,
     `DecidedAt` = decided, `Via`, `Late` (bool), `Reason` (truncated), `Nonce`.
   - No: **Create item FleetApprovals from decision** with the same columns plus `Digest`, `SourceFile`; the
     descriptive columns are filled in later by the `approval` case's "no summary" branch.
3. **Decision carries a nonce** (Condition): `empty(coalesce(J(nonce), ''))` is not equal to `true`.
   - Yes: **Get items FleetDecisions for mirror** `Title eq '@{J(nonce)}'`; **Decision row found for mirror**
     (Condition) > Yes: **Update item FleetDecisions applied**: `Title`=nonce, `Result` = `applied`,
     `ResultAt` = decided.

#### Case `notification`

1. **Get items FleetNotifications by key**: `Title eq '@{J(key)}'`.
2. **Compose notification is new** (Compose):
   `@or(equals(length(outputs('Get_items_FleetNotifications_by_key')?['body/value']), 0), greater(int(coalesce(J(seq), 0)), <row Seq as int, 0 when blank>))`
   (exact text in the definition file). A new file for an existing key is a *new* notification (the laptop
   only re-emits a key after its cooldown); the same file replayed has the same `seq` and is not.
3. **Notification is new** (Condition): the Compose output is equal to `true`.
   - Yes: **Notification row exists** (Condition) > Yes: **Update item FleetNotifications**; No: **Create item
     FleetNotifications**. Columns: `Title`=key, `Repo`, `Ticket`, `State`, `Severity`, `TitleText` (title),
     `Body` (body), `At`, `Seq`, `Quiet` (bool), `ApprovalId` (approval_id), `SourceFile` = trigger Name.
     Then **Notification should push** (Condition, run after the previous condition): `J(quiet)` is not equal
     to `true` **and** `coalesce(J(severity), '')` is not equal to `info` > Yes: **Send push notification V2
     agent**: Message = `Fleet: an agent needs you`, Parameters = `{"screen":"agent","repo":"@{J(repo)}"}`,
     other fields as in the approval push.

#### Case `heartbeat`

1. **Get items FleetHeartbeat**: `Title eq 'laptop'`.
2. **Heartbeat row exists** (Condition) > Yes: **Heartbeat file is newer** (Condition): `coalesce(J(at), '')` is
   greater than or equal to the row's `At` (ISO text compares lexicographically) > Yes: **Update item
   FleetHeartbeat**. No row: **Create item FleetHeartbeat**. Columns: `Title` = `laptop`, `At`, `EverySeconds`
   (every_s), `ExpireSeconds` (expire_s), `Contract`, `Operator`, `Bridge`, `LaptopId` (laptop_id), `ServeUp`
   (serve_up, bool), `DeskStreams` (desk_streams), `Repos`, `NeedsHuman`, `ApprovalsPending`, `Notifications24h`,
   `Rejected24h` (all from `counts.*`), `InboxLastSeen` (inbox_last_seen).

#### Case `result`

1. **Get items FleetDecisions by nonce**: `Title eq '@{J(nonce)}'`.
2. **Decision row exists for result** (Condition) > Yes: **Update item FleetDecisions result**; No: **Create
   item FleetDecisions from result** (`Kind` = kind_of, the rest empty). Result columns: `Result` =
   `@if(equals(J(ok), true), 'applied', 'rejected')`, `ResultCode` = code, `ResultText` =
   `trim(concat(error, ' ', hint))` truncated 255, `ResultAt` = at.
3. **Result rejects a decision** (Condition): `coalesce(J(kind_of), '')` is equal to `decision` **and** `J(ok)`
   is not equal to `true` > Yes: **Get items FleetApprovals by nonce** `Nonce eq '@{J(nonce)}'`; **Approval row
   found by nonce** (Condition) > Yes: **Update item FleetApprovals rejected**: `Title` = the row's Title,
   `Status` = `rejected`, `ResultCode`, `ResultText`.

### 5. **Catch** (Scope), **Settings > Run after** Try: *has failed*, *has timed out*

1. **Filter array failed actions**: From `@result('Try')`, condition `@equals(item()?['status'], 'Failed')`.
2. **Compose failure text**: `run <workflow()?['run']?['name']> file <trigger Name>: <first failed action's
   error>` truncated to 300 (exact text in the definition). `result()` only reports the scope's *top-level*
   actions (Get file content, Parse JSON, the Switch), so a failure deep inside a case reads as the Switch's
   generic "An action failed" message; the run id in the text is how the operator opens the run history.
3. **Create item FleetNotifications alert** (Retry Policy None): `Title` =
   `flow-failed:FleetOutboxToLists:<run name>`, `State` = `error`, `Severity` = `alert`, `TitleText` =
   `Flow FleetOutboxToLists failed`, `Body` = the Compose output, `At` = `@utcNow('yyyy-MM-ddTHH:mm:ssZ')`,
   `Seq` = `0`, `Quiet` = `false`, `SourceFile` = trigger Name, the rest empty.

If the Catch itself fails (SharePoint down) the run fails visibly in run history; a flow that fails continuously
for 14 days is turned off by the platform (Q11), which is why the alert row is a list row and not another push.

## Build sheet: `FleetDecide`

**Solutions > FleetAgent > New > Automation > Cloud flow > Instant**, trigger **Power Apps (V2)**. Add the inputs
**in this order** (the designer names them `text`, `text_1` ... `text_8` and `number` internally, in the order
added; the expressions below depend on that order):

| # | Input | Type | Internal key | Passed by the app |
|---|---|---|---|---|
| 1 | `Kind` | Text | `text` | `decision` or `reply` |
| 2 | `ApprovalId` | Text | `text_1` | `FleetApprovals.Title` for a decision, else `""` |
| 3 | `Repo` | Text | `text_2` | repo alias for a reply, else `""` |
| 4 | `Decision` | Text | `text_3` | `approved` or `denied` for a decision, else `""` |
| 5 | `Reason` | Text | `text_4` | required when denied, else may be `""` |
| 6 | `Message` | Text | `text_5` | reply text or `""` |
| 7 | `AnswersJson` | Text | `text_6` | `[{"id":"q1","answer":"..."}]` or `""` |
| 8 | `Digest` | Text | `text_7` | the row's `Digest` (64 lowercase hex) for a decision, else `""` |
| 9 | `ExpiresSeconds` | Number | `number` | the laptop's `FleetHeartbeat.ExpireSeconds` (900 by default); `0` means 900 |
| 10 | `Device` | Text | `text_8` | a short device label, may be `""` |

All ten are required (the designer default); the app always passes all ten. Adding an input or removing a
response output later breaks the published app, so copy the flow to change it (Q6).

**Flow details > Run only users > Edit**: share with the operator; under *Connections Used* set **Office 365
Users** to **Provided by run-only user** (keep OneDrive and SharePoint on the owner's connections), then re-add
the flow in the app and save the app (known issue, Q6).

### 1. **Try** (Scope), containing steps 2-16

2. **Get my profile (V2)** (Office 365 Users, `MyProfile_V2`), no parameters.
3. **Compose validation error** (Compose): the nested `if(...)` in the definition
   (`Try.actions.Compose_validation_error.inputs`, 1,732 characters, under the 8,192 limit). It returns `''`
   when the input is valid, else one sentence: `Kind must be decision or reply.` / `ApprovalId is required for a
   decision.` / `Decision must be approved or denied.` / `A reason is required when denying.` / `Digest must be
   64 lowercase hex characters.` / `Repo is required for a reply.` / `A reply needs a message or answers.`
   The hex check is `length = 64` plus sixteen chained `replace()` calls (the expression language has no regex);
   the app should also `IsMatch(digest, "^[0-9a-f]{64}$")` so a bad value never leaves the phone.
4. **Reject invalid input** (Condition): `outputs('Compose_validation_error')` is not equal to `''`.
   Yes: **Respond invalid input** (Respond to a PowerApp or flow: `ok` = No, `nonce` = `''`, `inboxFile` = `''`,
   `error` = the Compose output) then **Terminate after invalid input** (Control > Terminate, Status
   Succeeded). Nothing is written.
5. **Compose nonce**: `@replace(guid(), '-', '')`.
6. **Compose issued**: `@utcNow('yyyy-MM-ddTHH:mm:ssZ')`.
7. **Compose expires**: `@addSeconds(outputs('Compose_issued'), if(greater(int(coalesce(triggerBody()?['number'], 900)), 0), int(coalesce(triggerBody()?['number'], 900)), 900), 'yyyy-MM-ddTHH:mm:ssZ')`.
8. **Compose by**: `@coalesce(body('Get_my_profile_(V2)')?['userPrincipalName'], body('Get_my_profile_(V2)')?['mail'], '')`.
9. **Compose decision record**: the object `{"schema": 1, "kind": "decision", "nonce": ..., "issued": ...,
   "expires": ..., "by": ..., "id": trim(ApprovalId), "digest": trim(Digest), "decision": trim(Decision),
   "reason": Reason, "device": trim(Device)}` (values are the Compose outputs and `triggerBody()` fields).
10. **Compose reply record**: `{"schema": 1, "kind": "reply", "nonce", "issued", "expires", "by", "repo":
    trim(Repo), "message": Message, "answers": @json(if(empty(trim(AnswersJson)), '[]', AnswersJson)),
    "device"}`. Invalid `AnswersJson` fails here and surfaces through the Catch as `ok` = No.
11. **Compose record**: `@if(equals(trim(coalesce(triggerBody()?['text'], '')), 'decision'), outputs('Compose_decision_record'), outputs('Compose_reply_record'))`.
12. **Compose inbox file name**: `@concat(trim(coalesce(triggerBody()?['text'], '')), '-', outputs('Compose_nonce'), '.json')`.
13. **Create file** (OneDrive for Business, `CreateFile`): Folder Path = `fleet_FleetInboxFolderPath`,
    File Name = `outputs('Compose_inbox_file_name')`, File Content = `@string(outputs('Compose_record'))`.
    A name collision is impossible in practice (fresh GUID); if it ever happens the action fails and the app
    gets `ok` = No, which is the right outcome (Q1: treat "already exists" as "already answered").
14. **Create item FleetDecisions** (Retry Policy None): `Title` = nonce, `Kind`, `ApprovalId`, `Repo`,
    `Decision`, `Reason` (truncated 255), `Message`, `AnswersJson`, `Digest`, `By` = Compose by, `Device`,
    `Issued`, `Expires`, `InboxFile`, `Result` = `sent`, `ResultCode`/`ResultText`/`ResultAt` empty.
15. **Mark approval sent** (Condition): `trim(Kind)` is equal to `decision` > Yes: **Get items FleetApprovals
    by id** `Title eq '@{trim(ApprovalId)}'`; **Approval row found** (Condition) > Yes: **Update item
    FleetApprovals sent** (Retry Policy None): `Title` = ApprovalId, `Status` = `sent`, `DecidedBy` = Compose
    by, `DecidedAt` = issued, `Nonce` = nonce, `Via` = `mobile`.
16. **Respond ok** (Respond to a PowerApp or flow): outputs named exactly `ok` (Yes/No) = Yes, `nonce` (Text),
    `inboxFile` (Text), `error` (Text) = `''`.

### 17. **Catch** (Scope), Run after Try: *has failed*, *has timed out*

1. **Filter array failed actions**: From `@result('Try')`, `@equals(item()?['status'], 'Failed')`. Here the
   write steps *are* top-level in Try (validation ends the run with Terminate instead of nesting them), so the
   text names the failed step and its connector error.
2. **Compose failure text**: `FleetDecide run <run name>: <error>` truncated to 300.
3. **Respond failure**: `ok` = No, `error` = the text, and `nonce` / `inboxFile` =
   `@if(equals(actions('Create_file')?['status'], 'Succeeded'), string(actions('Compose_nonce')?['outputs']), '')`
   (and the same for the file name). A non-empty `inboxFile` with `ok` = No means the file *was* written and the
   laptop will act on it; the app must show "sent, but the audit row failed" and not offer a resend (a resend
   would be rejected by the laptop as `mobile_already_decided` anyway).

App side, for reference: `Set(r, FleetDecide.Run("decision", ThisItem.Title, "", "approved", "", "", "",
ThisItem.Digest, Value(LookUp(FleetHeartbeat, Title = "laptop").ExpireSeconds), "phone"))`, then `r.ok`,
`r.nonce`, `r.inboxfile`, `r.error` (Power Apps lower-cases output names in the record).

## Retry and idempotency rules

- The platform delivers at-least-once (Q2): a run can repeat, and a Low-profile owner gets up to 2 automatic
  retries ~5-10 minutes apart on 408/429/5xx. **Retry Policy = None on every SharePoint Create item / Update
  item**; everything else keeps the default.
- Every write is an upsert keyed by `Title` (repo, approval id, key, `laptop`, nonce) preceded by a Get items.
  A replayed file finds its row and either updates it with identical values or, for `attention`, `notification`
  and `heartbeat`, skips because the file is not newer than the row (`Seq` / `At`). Two files of the same key in
  one poll may run in parallel; the same newer-than check makes the order irrelevant.
- Pushes are sent only on the branch that created the approval row or found a genuinely new notification, so a
  replay never pushes twice.
- `FleetDecide` writes nothing before validation passes; its nonce is fresh per run, so a retry from the app is
  a second decision the laptop rejects (`mobile_already_decided`), never a duplicate apply.
- The laptop writes each outbox file once, atomically, with a unique name (Q4/Q8), so "files moved within
  OneDrive are not new" (Q1) never bites.
- Keep bursts under about 30 new files per poll (Q1 known issue): the heartbeat is one file per five minutes and
  attention files are written only when a repo's digest changes; a laptop that comes back online after hours
  can exceed it, and the laptop's pruning of decided approvals and old notifications is the control.

## Request budget

Owner: a Microsoft 365 seeded user, 6,000 Power Platform requests per 24 h (official per-user limit; during the
transition period the enforced number is 10,000 per cloud flow per day for Low-profile flows and 200,000 for
Power Apps-triggered ones, capped at 100,000 per 5 minutes, Q11). Every executed action counts, including
Scope, Condition, Switch, Compose and retries; an empty poll that starts no run does not.

| Run | Actions counted (trigger + Try scope + steps) | Files/day | Requests/day |
|---|---|---|---|
| `heartbeat` (every 300 s) | trigger, Try, Get file content, Parse JSON, Switch, Get items, 2 Conditions, Update item = 9 | 86,400 / 300 = **288** | **2,592** |
| `attention` (a file per state change per repo) | 9-10 | ~80 (4 repos x 20 changes) | ~800 |
| `notification` | 11-12 (+1 push) | ~30 | ~350 |
| `approval` + `decision` mirror + `result` | 10 + 12 + 10 | ~10 cycles | ~320 |
| `FleetDecide` | ~17 | ~10 | ~170 |
| **Total** | | | **~4,200** (~70% of 6,000) |

The heartbeat is 60% of the bill. If the day's total ever nears 6,000, double `every_s` to 600 (144 files,
1,296 requests) before touching anything else; the phone's "laptop not syncing" rule is `now - At > 3 x
EverySeconds`, so it adapts by itself. Two other consequences of the same table: the 90-day
"no trigger activity" switch-off can never happen while the laptop heartbeats (Q11), and the OneDrive
connector's 100 calls/minute is nowhere near reached (2 calls per run, at most 20 runs per poll).

## DLP checks (before building)

1. In the Power Platform admin center, **Data policies** for the target environment: SharePoint, OneDrive for
   Business, Power Apps Notification (v1 and v2), Microsoft 365 Users and Excel Online (Business) must sit in
   the **same** group (Business). They cannot be blocked, only classified, and Microsoft's default-environment
   guidance moves them into Business together (Q10).
2. **Connector action control**: no rule blocking OneDrive `Get file content` / `Create file` or SharePoint
   `Create item` / `Update item` / `Get items`; since October 2024 action control also governs triggers.
3. A managed default environment with an **advanced connector policy** (allowlist) can restrict even these; ask
   for the list.
4. The Power Apps (V2) trigger and Data Operations (Compose, Parse JSON, Filter array) are platform capabilities,
   not connectors, and appear in no classification list (UNVERIFIED that they can never be restricted).
5. A violation blocks Save at design time; a policy change afterwards suspends the flow within 24 hours with
   `FlowSuspensionReason=CompanyDlpViolation`, re-activated within 7 days once compliant.

## Import sheet

For the day the two flows work in the operator's tenant:

1. Build both flows inside one unmanaged solution (**FleetAgent**, publisher prefix `fleet`) so they bind to
   connection references and environment variables rather than to raw connections (Q9). Microsoft 365 users
   can create solution-aware flows in any environment with a Dataverse database; the default environment has one.
2. Clear the *current value* of each environment variable (keep the default empty too), then **Solutions >
   FleetAgent > Export > Unmanaged**. The zip holds `solution.xml`, `customizations.xml`, `[Content_Types].xml`
   and `Workflows/FleetOutboxToLists-<guid>.json`, `Workflows/FleetDecide-<guid>.json` (multi-line JSON).
3. Diff each `Workflows/*.json` against the file here (`properties.definition.actions` is the part that matters;
   the export adds `metadata.operationMetadataId` GUIDs and connection-reference names of its own). Where they
   differ, the export wins: update the definition files here from the export, and delete the
   `_comment_unverified` keys that the export has settled.
4. **Check the zip in under `mobile/flows/solution/`** (one zip per export, name with the date), next to these
   definitions. The zip is the importable artifact; the JSON stays the reviewable one.
5. To import elsewhere (or after a reset): **Solutions > Import solution > Browse** the zip > Next > map the four
   connection references to existing connections (create them first, signed in as the operator) > enter the
   five environment variable values > Import. Flows are turned off and on during import and the importer becomes
   their owner; `ConnectionAuthorizationFailed` on turn-on means a connection the importer does not own.
6. After import: re-pick the outbox folder in the trigger if the folder ID variable was left empty, set the
   `FleetDecide` run-only users again (that setting is not part of the solution), re-add the flow in the app,
   and run the test plan.

If solution import is blocked in the tenant, fall back to **Export > Package (.zip)** / **Import Package
(Legacy)** (incompatible with solutions), and only then to rebuilding from this sheet; the new designer can paste
individual actions and whole Scopes/Conditions from the clipboard (**Copy action** / **Paste an action**) but not
triggers or a whole definition.

## Verify on import

Spots in the definition files whose exact wire shape was **not** verified against a Microsoft page. Each has a
`_comment_unverified` key next to it naming the row below. The claim that the designer and the importer *ignore*
unknown keys is itself unverified; if an import or Save complains, strip them first:
`python -c "import json,sys; strip=lambda o:{k:strip(v) for k,v in o.items() if not k.startswith('_comment')} if isinstance(o,dict) else [strip(i) for i in o] if isinstance(o,list) else o; p=sys.argv[1]; json.dump(strip(json.load(open(p,encoding='utf-8'))),open(p,'w',encoding='utf-8'),indent=2,ensure_ascii=False)" mobile/flows/FleetDecide.definition.json`
(run it on a copy; the committed files keep their comments).

| # | Where | What is assumed | How to verify / fix |
|---|---|---|---|
| 1 | every SharePoint action, `inputs.parameters` | Site Address is `dataset`, List Name is `table` | open any SharePoint action's Code view after building it by hand; rename if different |
| 2 | every SharePoint action | `table` accepts the list *name*; Create/Update item columns are flattened `item/<Column>` keys | the designer stores the list GUID; pick the list from the dropdown when building; compare Code view |
| 3 | trigger `folderId` | an environment variable holding the folder ID works in the trigger's Folder | if the trigger errors, pick the folder in the picker instead (the stored value is the ID to copy into the variable) |
| 4 | trigger `splitOn`, `recurrence` | `@triggerOutputs()?['body/value']` and a 5-minute recurrence | Code view of the trigger after saving with Split On on |
| 5 | Parse JSON `content` | with Infer Content Type = No the body is `{$content-type, $content}` and `base64ToString($content)` gives the text | if Parse JSON reports "Expected Object but got String/Null": use `@json(string(body('Get_file_content')))`, or set Infer Content Type = Yes and use `@body('Get_file_content')` directly (the connector then returns `application/json` for `.json` files) |
| 6 | Send push notification V2 parameters | `playerType` = `PowerApps` for *Mobile app = Power Apps*; `recipients` is a one-element array; `dynamicParams` is an object | build one push action by hand, compare Code view; Parameters may be stored as JSON text |
| 7 | Create file `body` | a JSON string is uploaded as UTF-8 text bytes | open the produced inbox file in the laptop's `rejected/` sidecar if the laptop reports `mobile_bad_json`; the laptop reader is BOM-tolerant either way |
| 8 | Power Apps (V2) trigger | `type: Request`, `kind: PowerAppV2`, keys `text`, `text_1`..`text_8`, `number`, `x-ms-dynamically-added` / `x-ms-content-hint` | add the ten inputs in order and compare Code view; if the keys differ, re-point every `triggerBody()?['...']` |
| 9 | Respond to a PowerApp or flow | `type: Response`, `kind: PowerApp`, output schema with `x-ms-dynamically-added` | Code view after adding the action with the four outputs |
| 10 | `retryPolicy` | lives under `inputs` as `{"type": "none"}` | Settings > Networking > Retry Policy = None, then Code view |
| 11 | `connectionReferences` block | keys equal the `host.connectionName`; `runtimeSource` is `embedded` for the maker's connection and `invoker` for *Provided by run-only user* | compare with the exported `Workflows/*.json` |
| 12 | environment variable parameters | definition parameter key `fleet_X (fleet_X)` with `metadata.schemaName` | compare with the export; the prefix is the publisher's |
| 13 | Catch (both flows) | `result('Try')` items expose `status` and `error`; `actions('X')?['status']` / `?['outputs']` are null-safe for a skipped action | force one failure (rename a list) and read the alert row / app error |
| 14 | `FleetDecide` Terminate | a Terminate (Succeeded) inside a Scope inside a Condition ends the run after the response is sent | call with `Kind = "x"`: the app must get `ok` = No and no file/row may appear |
| 15 | `utcNow('yyyy-MM-ddTHH:mm:ssZ')` | `T` and `Z` pass through as literals (they are not .NET format specifiers) | check `issued` in a test decision file: `2026-09-26T09:14:05Z`, 20 characters |
| 16 | `first([])` | returns null (not an error) when Get items finds no row, so the `?['Seq']` / `?['At']` lookups fall back to `'0'` / `''` | seed an attention file for a repo with no row; the Create branch must run without an expression error |
| 17 | Get my profile (V2) output | property names are camelCase (`userPrincipalName`, `mail`) | the SDK model uses `userPrincipalName`; confirm in the run's outputs |
| 18 | OneDrive Create file collision | an existing name fails the action instead of overwriting | not reachable with GUID nonces; do not enable any overwrite option |
| 19 | 255-character single-line columns | `Summary`, `Reason`, `ResultText` are truncated by the flow; `ApprovalsJson` is written whole | if an attention update ever fails on `ApprovalsJson` length (8 x 96-character ids), switch that column to *Multiple lines of text* (plain); no rename needed |

## Test plan

Prerequisites: both flows on, the five lists created from `../data/FleetAgent.xlsx` with the sample rows deleted,
`FleetAgent/outbox/{attention,approvals,notifications,heartbeat,results}` and `FleetAgent/inbox` existing in the
operator's OneDrive, the app installed on the phone and opened once, OS notifications allowed.

1. **Outbox to row.** Copy `samples/heartbeat-20260926-0915.json` into `FleetAgent/outbox/heartbeat/` (any
   unique name ending in `.json`). Within one poll (up to 5 minutes) a `FleetOutboxToLists` run appears; the
   `FleetHeartbeat` row `laptop` shows `At` = `2026-09-26T09:15:00Z`, `Repos` = `3`, `ServeUp` = `true`.
   Copy the same file again under a new name: a second run, no change (not newer). Copy
   `samples/attention-luna-187.json` into `attention/`: the `luna` row appears with `NeedsHuman` = `true`,
   `QuestionsJson` holding the question array as text, `Seq` = `187`.
2. **Approval to push.** Copy `samples/approval-rdsd-uat-7f3a.json` into `approvals/`. Expect the
   `FleetApprovals` row (`Status` = `pending`, `SourceFile` = the file name) and, on the phone, "An agent is
   waiting for your approval" with the generic Power Apps icon; tapping it opens the app with
   `Param("screen") = "approval"` and `Param("approvalId")` = the id. Copy the file again under another name:
   no second push. Copy `samples/notification-luna-needs_human-187.json` into `notifications/`: row
   `luna:needs_human`, push "Fleet: an agent needs you". Note the elapsed time from copy to push (budget:
   ~1 min best, 4-8 min typical, Q7).
3. **Decide from the app.** Open the pending approval and approve it. `FleetDecide` responds within seconds
   with `ok` = Yes and a nonce; the `FleetDecisions` row exists with `Result` = `sent`, `By` = the operator's
   UPN, `InboxFile` = `decision-<nonce>.json`; the `FleetApprovals` row reads `Status` = `sent`, `Via` =
   `mobile`, `Nonce` = the nonce; and `FleetAgent/inbox/decision-<nonce>.json` appears in the laptop's synced
   folder with exactly `schema, kind, nonce, issued, expires, by, id, digest, decision, reason, device`,
   `issued`/`expires` 20-character UTC stamps, `expires - issued` = the `ExpiresSeconds` passed.
4. **Laptop applies.** The laptop's bridge verifies the file (nonce unused, operator matches, digest matches,
   not expired) and applies it; it writes `outbox/approvals/<id>.decision.json` (via `mobile`, the nonce) and
   `outbox/results/<nonce>.result.json` (`ok` = true). After the next poll the `FleetApprovals` row reads
   `Status` = `approved`, `DecidedBy` = the UPN, `Late` = `false`, and the `FleetDecisions` row `Result` =
   `applied` with `ResultAt`.
5. **Rejected path.** Copy `samples/result-c0d3e6f9-rejected.json` into `results/` after creating a
   `FleetDecisions` row titled `c0d3e6f9a2b5c8d1e4f7a0b3c6d9e2f5` and a `FleetApprovals` row whose `Nonce` is
   that value: the decision row turns `rejected` with `ResultCode` = `mobile_expired` and the approval row
   `Status` = `rejected`.
6. **Validation.** From the app (or the flow's Test pane) call `FleetDecide` with `Kind` = `x`, then with
   `Kind` = `decision`, `Decision` = `denied`, `Reason` = `""`, then with a 63-character digest: each returns
   `ok` = No with the matching sentence, and no file or row is written.
7. **Catch.** Rename the `FleetNotifications` list for a minute and drop a notification file: a
   `FleetNotifications` row `flow-failed:FleetOutboxToLists:<run>` cannot be written either, so the run shows
   as failed in run history; rename back, drop the file again, and confirm the alert path by instead renaming
   `FleetAttention` and dropping an attention file (the alert row appears with `Severity` = `alert`).
8. **Budget.** After a full day, read **Analytics > Usage** (or the flow's run counts) and compare with the
   table above.
