# Step 02: the lists, the bridge library, and the Owners-only lock

**Who:** you. The operator approves the SharePoint connection the first time it is used.
**Produces:** on `siteUrl`:
- the five lists `FleetAttention`, `FleetApprovals`, `FleetDecisions`, `FleetNotifications` and `FleetHeartbeat`,
  with every column of the contract and an index on `Title` and `Operator`;
- the document library `library` (default `FleetAgent`), with one folder per operator named by their UPN;
- all six locked to the site's **Owners** group: Full Control for that group and nobody else.

No tool you have can create a SharePoint list directly. All of this is done by a one-shot flow,
`FleetProvisionLists`, which `build/prepare.py` writes from the pinned contract and the config. The flow is safe to
run more than once:

- it creates a list, column or folder only when it is missing;
- it turns an index on, which changes nothing when it is already on;
- it deletes nothing but permissions: on each list and the library it removes every role assignment except the
  Owners group's.

## 1. Generate the flow

```
python build/prepare.py lists
```

This writes `build/out/FleetProvisionLists.json`. What the file holds:

- **`definition`**: one Compose (`Spec`) holding the five lists and the library, then loops that call SharePoint's
  **Send an HTTP request to SharePoint** (`HttpRequest`), in this order:
  1. the lists and their columns;
  2. the indexes;
  3. each operator's folder in the library;
  4. the lock: break inheritance without copying anyone, grant the Owners group Full Control, remove everyone
     else, and read the assignments back into `Owners_only`.
- **`connectionRefsTemplate`**: the `connectionRefs` argument, with the connection name left blank.

The column rules come from the contract and `data/README.md`:

| Rule | Detail |
| --- | --- |
| type | every column is text |
| multi-line columns | *Multiple lines of text*, plain (not rich text): `Says`, `ApprovalsJson`, `QuestionsJson`, `PayloadPreview`, `Message`, `AnswersJson` and `Body` |
| internal names | exactly the contract's names (option 25 sets this) |
| skipped columns | `Title` and `Created`, which every list already has (`build/README.md` §The Created column) |
| `Operator` | on every list; with `Title` it identifies a row, so both are indexed |

## 2. The connection

Call FlowAgent `pick_or_create_connection` for `shared_sharepointonline`. If it opens a consent window, tell the
operator to approve it. Put the returned connection name into the template's `connectionName`. Record it under
`connections` in the state file; steps 03 and 05 reuse it.

The connection must belong to a site **Owner**. Breaking a list's inheritance and changing its permissions needs
the Manage Permissions right that Owners have; anyone else gets a 403 at `Break_inheritance`.

## 3. Create, turn on, run

1. Call `preflight_flow` (or `validate_flow`) with the definition and the connection references.
   - If it reports that the `HttpRequest` parameter names differ (`dataset`, `parameters/method`,
     `parameters/uri`, `parameters/headers`, `parameters/body`), call `get_operation_details` for
     `shared_sharepointonline` / `HttpRequest`.
   - Correct the names in `build/prepare.py`'s `_sp()` (a tracked fix), run `python -m pytest -q`, and
     regenerate.
2. Call `list_flows`. If `FleetProvisionLists` exists, call `update_flow` on it. Otherwise call `create_flow` with
   name `FleetProvisionLists`, the definition and the connection references.
3. Call `publish_flow` to turn it on.
4. Call `run_flow` with `wait: true`.
5. On a failed run, call `diagnose_run`. The usual causes:
   - **403:** the connection's account is not an Owner of the site. Ask the operator to fix that first.
   - **400 on `CreateFieldAsXml`:** read the message. A duplicate display name means a column was made by hand
     under another internal name; tell the operator which one.
   - **400 on `folders/add`:** an operator's UPN holds a character SharePoint refuses in a folder name. The config
     check refuses most of them; report the one it missed.

## 4. Check, then remove the flow

Run the flow a second time with `run_flow` and `wait: true`. Then call `get_run_actions`, and
`get_run_action_repetitions` for the loops.

**Check:**

- In the second run, every `Create_list`, `Create_column` and `Create_folder` was skipped, and so was every
  `Break_inheritance`. That proves everything exists and is already locked.
- For each list, `Select_field_names` contains every column of its `Spec` entry.
- `Select_folder_names` contains every UPN in `operators`.
- **Every `Owners_only` repetition, six of them, shows `ownersOnly: true`.** Any `false` means someone other than
  the Owners group can still read that list or the library. Mark the step `blocked` and give the list's name.

Then delete the provisioning flow with `delete_flow`; `prepare.py lists` can regenerate it at any time. Record
step 02 as `done`, with the column counts per list:

| List | Columns |
| --- | --- |
| FleetAttention | 27 |
| FleetApprovals | 21 |
| FleetDecisions | 18 |
| FleetNotifications | 12 |
| FleetHeartbeat | 15 |

Each count is in addition to `Title`.

Tell the operator, in one line: the lists and the bridge library are readable by the site's Owners only, so anyone
later made an Owner of the site can read every operator's fleet too.

**Fallback,** only if the HttpRequest action is blocked by the tenant's DLP policy: the operator creates the lists
by hand from `data/FleetAgent.xlsx` following `data/README.md`, the library and folders in SharePoint, and the
permissions under each one's **Settings** > **Permissions for this list** > **Stop inheriting permissions**,
removing everyone but the Owners group. Mark the step `waiting` until they say it is done.
