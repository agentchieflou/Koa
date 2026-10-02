# Step 05: the FleetOutboxToLists flow

**Who:** you. The operator approves the Power Apps Notification connection.
**Produces:** `outboxFolderId` in the config, and `FleetOutboxToLists` turned on. It reads every file the laptop
writes under `outbox/`, upserts the matching list row, and pushes a content-free notification for approvals and
for alerts.

## 1. The outbox folder's id

The trigger, OneDrive's **When a file is created (properties only)** (`OnNewFilesV2`), takes a folder **id**, not
a path. Find the id of `outboxFolderPath` (for example `/FleetAgent/outbox`) with step 03's OneDrive connection:

1. Call `get_operation_details` for `shared_onedriveforbusiness` / `OnNewFilesV2`. Its `folderId` parameter names
   the dynamic tree the designer's folder picker uses.
2. Walk that tree with `invoke_operation` (or `resolve_params`): from the root to the bridge folder, then to
   `outbox`. The id is the `Id` of the `outbox` entry.
3. If the tree cannot be walked, call `invoke_operation` with OneDrive's **Get file metadata using path**
   (`GetFileMetadataByPath`) and `path` = `outboxFolderPath`. Its `Id` is the same value.

If neither works, ask the operator. It takes about two minutes:

> In https://make.powerautomate.com: **+ Create** > **Automated cloud flow** > skip > search the trigger
> **When a file is created (properties only)** (OneDrive for Business) > Folder: pick `FleetAgent` > `outbox`. Then
> open the trigger's **...** > **Peek code** (or **Code view**), copy the value of `folderId`, paste it here, and
> close the flow without saving.

Write the value as `outboxFolderId` in `build/fleet.config.json`.

## 2. Generate

```
python build/prepare.py flows
```

This now writes `build/out/FleetOutboxToLists.json` as well, with the site, the folder id, the app id (the push's
*Your app*) and the operator (the push's recipient) filled in.

## 3. Connections

| Connector | Mode | Connection |
| --- | --- | --- |
| `shared_onedriveforbusiness` | `Embedded` | step 03's |
| `shared_sharepointonline` | `Embedded` | step 02's |
| `shared_powerappsnotificationv2` | `Embedded` | `pick_or_create_connection`; the operator approves |

## 4. Create and turn on

1. Call `preflight_flow`, then `create_flow` (or `update_flow` if `list_flows` already shows
   `FleetOutboxToLists`), then `publish_flow`.
2. Fix only what a validator reports, in `flows/FleetOutboxToLists.definition.json` as a tracked fix, and record
   it in the matching "Verify on import" row of `flows/README.md`. The rows most likely to need it:
   - 3: the trigger's `folderId`;
   - 4: `splitOn` and recurrence;
   - 6: the push action's parameters;
   - 5: Parse JSON's `content`.

## 5. Check

The laptop writes a heartbeat file every 300 seconds while `ad-fleet serve` or `ad-fleet mobile watch` runs. If
neither is running, ask the operator to start one.

Within about ten minutes (the trigger polls every five), `get_run_history` for `FleetOutboxToLists` must show a
**Succeeded** run. Call `get_run_details` on it: the `Switch_on_kind` case taken is `Case_heartbeat` or
`Case_attention`.

A failed run is your next fix. Call `diagnose_run` on it. Parse JSON failures, wrong list names and push
parameters each have a row in `flows/README.md` "Verify on import".

Record the flow id under `flows.FleetOutboxToLists` and mark step 05 `done`.
