# Testing mobile prompting: the first round trips

How to get from this repository to a prompt typed on the phone reaching an agent on the laptop, and an
approval decided on the phone releasing one. It strings together the build sheets that already exist
(`data/README.md`, `flows/README.md`, `README.md`) in the order a first test needs them, and says what to
look at after each step. The laptop side is this-next-please's (`docs/fleet-mobile.md` there is its
contract page); nothing on the laptop is installed from here.

Every number this run produces (how long each leg took, whether a push arrived) is a row of
this-next-please's `docs/windows-verification.md` §Mobile, M1-M12, which all read *not yet measured*:
write what you saw there.

## What a prompt is, end to end

```
phone: AgentScreen > Reply > ReplyScreen > Send reply
  FleetDecide.Run("reply", "", <repo>, "", "", <message>, "", "", ExpireSeconds, Host.OSType)
    the flow: Get my profile (V2) -> by = your UPN; nonce = guid(); issued/expires
    OneDrive: FleetAgent/inbox/reply-<nonce>.json          (contract $defs/inbox_reply)
    FleetDecisions: a row, Result = sent
laptop: the bridge (ad-fleet serve, or ad-fleet mobile watch), every 5 s
    checks size, JSON, schema, nonce, time, expiry, operator, repo        (docs/fleet-mobile.md, the checks in order)
    a console the fleet opened -> typed in (via: say); anything else -> resumed headless (via: send)
    outbox/results/<nonce>.result.json                     (contract $defs/result)
phone: FleetOutboxToLists updates the FleetDecisions row: Result = applied | rejected, ResultText in the laptop's words
    AgentScreen > Last reply shows it after the next 60 s refresh
```

A reply carries text only; it never carries `force`, so a budget the laptop has spent stays spent. The
text reaches the agent exactly as typed and is not copied to any list but `FleetDecisions.Message`.

## 0. What you need

- The laptop on this-next-please at or after `913d157` (the bridge, `ad-fleet mobile`, the doctor rows),
  with OneDrive for Business syncing.
- A Microsoft 365 account with Power Apps and Power Automate under the seeded licence (every connector used
  is Standard), and a SharePoint site you can create lists on.
- Power Apps mobile on the phone, signed in as the same account the laptop's `fleet.mobile.operator` names.
- This repository, and `python -m pip install openpyxl` only if you regenerate the workbook.

## 1. The laptop: the bridge folder and the loop (once)

```
ad-setup --patch fleet.mobile            # enabled = true; folder = %OneDriveCommercial%/FleetAgent;
                                         # operator = your UPN; expire_s = 900; notify = true
ad-fleet mobile init                     # the eight directories and pairing.json, each only when missing
ad-doctor                                # fleet/mobile ok; a fail names its fix (attrib +p "<folder>" /s /d)
ad-fleet serve                           # the bridge runs as its thread; or `ad-fleet mobile watch` with no desk
ad-fleet mobile status                   # outbox{kind,files,newest}: a heartbeat within 300 s
```

Look at: `<folder>/outbox/heartbeat/<yyyymmdd-hhmm>.json` exists and the OneDrive icon on it turns to synced.
The folder must not be inside any checkout (`mobile_folder_in_repo`).

## 2. The tenant: lists, flows, app (once)

The quickest way is to let a Copilot agent do this section: [build/README.md](build/README.md). It runs the
checks below as part of its steps. By hand:

1. **The five lists**, from `data/FleetAgent.xlsx`: `data/README.md` §Creating the five lists. Every column
   text; delete the sample rows afterwards.
2. **`FleetOutboxToLists`**: `flows/README.md`, the build sheet. Point its trigger at
   `FleetAgent/outbox` with subfolders included.
   - Check: within one heartbeat (300 s) `FleetHeartbeat` has its one row, `Title = laptop`, and every
     registered repository has a `FleetAttention` row. If not, the flow's run history says which action failed;
     a Parse JSON failure there is a contract drift `tests/test_flows.py` should have caught, so report it.
3. **`FleetDecide`**: `flows/README.md`. Its connections are *Provided by run-only user*.
   - Check: run it once from the designer's Test with `Kind = reply`, a registered repo and a message. A
     `reply-<nonce>.json` lands in `FleetAgent/inbox/`, and on the laptop `ad-fleet mobile apply --dry-run` lists
     it as `would_apply`. (The real apply is the bridge's; `apply` without `--dry-run` beside a running serve is
     refused `mobile_serve_running` on purpose.)
4. **The app**: `README.md`, the Studio build sheet, steps 1-9. Publish, share with yourself, open it once in
   Power Apps mobile on the phone (pushes reach only a user who opened the app in the last 30 days).
   - Check: Settings shows you as signed in, the laptop's operator equal to you (no mismatch banner), and a
     heartbeat younger than 15 minutes (no "not syncing" banner).

## 3. The prompt round trip

1. On the laptop, start an agent the fleet supervises: headless, or a console the fleet opened. On the phone,
   Home > Attention > tap its row.
2. **Reply**, type one line (for example *"Summarise what you changed since the last turn."*), **Send reply**.
   - The phone says it was sent, or `Not sent: <the flow's error>` verbatim. Nothing else on the phone decides.
   - `FleetDecisions` has a row for the nonce with `Result = sent`.
3. Watch `FleetAgent/inbox/` on the laptop: `reply-<nonce>.json` arrives with the OneDrive sync, then moves to
   `processed/` within a tick (5 s) of arriving.
4. The agent receives the line: typed into its console (`via: say`) or resumed headless (`via: send`). The
   agent's event stream carries `mobile.reply {nonce, by, via, answered, words}`.
5. `outbox/results/<nonce>.result.json` syncs up; `FleetOutboxToLists` sets the `FleetDecisions` row to
   `Result = applied`. On the phone, the agent's page shows it under **Last reply** after the next refresh.
6. Time the four legs (send to inbox on the laptop, inbox to processed, processed to result in the list, list
   to the phone) and write them into M1 of the runbook.

Then the refusals, each of which must leave the agent untouched and say why on the phone:

| Try | Expect on the phone (`ResultText`, the laptop's words) | On the laptop |
| --- | --- | --- |
| Reply while the agent is mid-turn | nothing at first: the laptop retries every tick; `applied` after the turn ends, or `mid_turn` with `retried_s` once `expires` passes | the file waits in `inbox/` |
| Reply to an agent whose session is external | the **Reply** button is disabled with the laptop's sentence | nothing arrives |
| Sign in on the phone as another account | the mismatch banner; a sent reply comes back `mobile_wrong_operator` | `rejected/<name>.why.json` |
| Turn the laptop's sync off for longer than `expire_s` (900 s), then on | `mobile_expired` | `rejected/` |
| Lock the laptop (Win+L), reply to a console agent | `via: say`, or `console_unreachable` (runbook M3) | |

## 4. The approval round trip

1. Make an agent ask for an approval (`ad-fleet approvals` lists it). The push arrives ("An agent is waiting
   for your approval", nothing more on the lock screen); a tap opens **ApprovalScreen** on that approval.
2. Read the preview, **Approve...** (or **Deny...** with a reason), **Send**. `FleetApprovals.Status` walks
   `pending > sent > approved | denied`; the agent's gated command proceeds or is refused.
3. A decision the laptop refuses (an expired one, or a request decided on the laptop meanwhile) shows its
   `ResultText` on the card and under History, and **no decision is applied**: the agent's own approval
   timeout refuses the write.

## When something does not arrive

| Symptom | Where to look |
| --- | --- |
| No `FleetHeartbeat` row | `ad-fleet mobile status` (is the bridge running?); the folder synced?; `FleetOutboxToLists` run history |
| "Not syncing" banner on the phone | three heartbeats missed: serve stopped, the laptop asleep, or OneDrive paused |
| `Not sent: ...` on Send | `FleetDecide` run history; its connections must be the invoker's (run-only user) |
| `reply-<nonce>.json` never reaches the laptop | the folder is online-only: `attrib +p "<folder>" /s /d`; `ad-doctor` says so |
| The file sits in `inbox/` | `ad-fleet mobile apply --dry-run` names the check that would refuse it, or `mid_turn` |
| `rejected/` has it | `<name>.why.json`: `code`, `error`, `hint`, and `docs/fleet-mobile.md` §Refusals on the laptop |
| A list row never updates | the flow's run for that outbox file; a second copy of a file changes nothing by design |
