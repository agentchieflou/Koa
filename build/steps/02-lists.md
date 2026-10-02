# Step 02: the five lists

**Who:** you. The operator approves the SharePoint connection the first time it is used.
**Produces:** `FleetAttention`, `FleetApprovals`, `FleetDecisions`, `FleetNotifications` and `FleetHeartbeat` on
`siteUrl`, each with every column of the contract.

No tool you have can create a SharePoint list directly. The lists are made by a one-shot flow,
`FleetProvisionLists`, which `build/prepare.py` writes from the pinned contract. The flow is safe to run more than
once:

- it creates a list only when no list with that title exists;
- it creates a column only when the list has no column with that internal name;
- it never deletes or changes anything that already exists.

## 1. Generate the flow

```
python build/prepare.py lists
```

This writes `build/out/FleetProvisionLists.json`. What the file holds:

- **`definition`**: one Compose (`Spec`) holding the five lists and their columns, then two loops that call
  SharePoint's **Send an HTTP request to SharePoint** (`HttpRequest`).
- **`connectionRefsTemplate`**: the `connectionRefs` argument, with the connection name left blank.

The column rules come from the contract and `data/README.md`:

| Rule | Detail |
| --- | --- |
| type | every column is text |
| multi-line columns | *Multiple lines of text*, plain (not rich text): `Says`, `ApprovalsJson`, `QuestionsJson`, `PayloadPreview`, `Message`, `AnswersJson` and `Body` |
| internal names | exactly the contract's names (option 25 sets this) |
| skipped columns | `Title` and `Created`, which every list already has (`build/README.md` §The Created column) |

## 2. The connection

Call FlowAgent `pick_or_create_connection` for `shared_sharepointonline`. If it opens a consent window, tell the
operator to approve it. Put the returned connection name into the template's `connectionName`. Record it under
`connections` in the state file; steps 03 and 05 reuse it.

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
   - **403:** the operator cannot create lists on that site. Ask for another site, or for Edit/Owner rights.
   - **400 on `CreateFieldAsXml`:** read the message. A duplicate display name means a column was made by hand
     under another internal name; tell the operator which one.

## 4. Check, then remove the flow

Run the flow a second time with `run_flow` and `wait: true`. Then call `get_run_actions`, and
`get_run_action_repetitions` for the loops.

**Check:**

- In the second run, every `Create_list` and every `Create_column` was skipped. That proves everything exists.
- For each list, `Select_field_names` contains every column of its `Spec` entry.

Then delete the provisioning flow with `delete_flow`; `prepare.py lists` can regenerate it at any time. Record step
02 as `done`, with the column counts per list:

| List | Columns |
| --- | --- |
| FleetAttention | 26 |
| FleetApprovals | 20 |
| FleetDecisions | 17 |
| FleetNotifications | 11 |
| FleetHeartbeat | 15 |

Each count is in addition to `Title`.

**Fallback,** only if the HttpRequest action is blocked by the tenant's DLP policy: the operator creates the lists
by hand from `data/FleetAgent.xlsx`, following `data/README.md`. Mark the step `waiting` until they say it is done.
