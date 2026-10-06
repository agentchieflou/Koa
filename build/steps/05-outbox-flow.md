# Step 05: the FleetOutboxToLists flows, one per operator

**Who:** you. The operator approves the Power Apps Notification connection, and changes each copy's primary owner.
**Produces:** one copy of `FleetOutboxToLists` per operator, named `FleetOutboxToLists (<UPN>)`, turned on. Each copy:
- **Trigger:** every file that operator's laptop writes under `<library>/<their UPN>/outbox/`, and no one else's.
- **Rows:** the matching list row is upserted and keyed by that operator and the row's `Title`.
- **Pushes:** a content-free push goes to that operator alone, for approvals and alerting notifications.

Why one copy each: a cloud flow on an Office 365 licence may make 10,000 requests a day, and one laptop costs about
4,500. One flow for three laptops would be throttled and, after 14 days of it, turned off. `flows/README.md`
§Request budget has the numbers.

## 1. Generate

```
python build/prepare.py flows
```

This writes `build/out/FleetOutboxToLists (<UPN>).json` for each UPN in `operators`, with the site, the library,
the app id (the push's *Your app*) and that operator filled in. There is no folder id to find:
- the trigger is SharePoint's **When a file is created (properties only)** on the folder `/<library>/<UPN>`;
- a trigger condition keeps only `.json` files under that operator's `outbox/`.

## 2. Connections

Every copy uses the same two connections:

| Connector | Mode | Connection |
| --- | --- | --- |
| `shared_sharepointonline` | `Embedded` | step 02's: a site Owner's, which can read every operator's folder |
| `shared_powerappsnotificationv2` | `Embedded` | `pick_or_create_connection`; the operator approves |

## 3. Create and turn on, for each operator

1. Call `preflight_flow`, then `create_flow` with the file's `name` (or `update_flow` if `list_flows` already shows
   it), then `publish_flow`. Record the id under `flows."FleetOutboxToLists (<UPN>)"`.
2. Fix only what a validator reports, in `flows/FleetOutboxToLists.definition.json` as a tracked fix, and record
   it in the matching "Verify on import" row of `flows/README.md`. Then regenerate and update every copy. The rows
   most likely to need it:
   - 3: the library trigger's parameters, `folderPath` among them;
   - 20: the trigger condition on `{Path}`;
   - 4: `splitOn` and recurrence;
   - 6: the push action's parameters;
   - 5: Parse JSON's `content`.

## 4. Give each copy to its operator

You create every copy, so every copy is yours: today each one has its own 10,000 a day, but once Microsoft's
licensing transition ends an automated flow runs on its owner's 6,000 a day, and yours would carry all of them.
Send the operator this, once, listing the copies:

> For each `FleetOutboxToLists (<UPN>)` flow, about a minute each:
>
> 1. In Power Automate, **My flows**, open the flow.
> 2. **Details** > **Edit**. Under **Primary owner**, remove yourself, enter that UPN, and **Save**.
> 3. **Edit** the flow and **Save** it once without changes, so it takes the new owner's limits at once.
>
> If **Details** has no **Primary owner**, the flow isn't in a solution yet: **Solutions** > **New solution**
> (name `FleetAgent`, publisher prefix `fleet`) > open it > **Add existing** > **Automation** > **Cloud flow** >
> **Outside Dataverse** > select the copies > **Add**. Then change the owners as above.
>
> Your own copy stays yours. You stay a co-owner of the others, and they keep using your connections.

Mark the step `waiting` until they say it is done. If they would rather leave it, record that in the state file's
notes: nothing breaks today, and `flows/README.md` §Request budget says what changes later.

## 5. Check

A copy has nothing to read until its operator's laptop writes into its folder. If none has yet, ask the operator
running the build to connect their own laptop now, following [build/each-operator.md](../each-operator.md). It
takes about five minutes. Then, for that operator's copy:

1. Within about ten minutes (the trigger polls every five, and the laptop writes a heartbeat every 300 seconds),
   `get_run_history` for that copy must show a **Succeeded** run.
2. Call `get_run_details` on it:
   - `Compose_operator` must be that operator's UPN, lowercase;
   - the `Switch_on_kind` case taken is `Case_heartbeat` or `Case_attention`.
3. **No run at all,** while the heartbeat file is in the library under the operator's folder: the trigger's
   folder or its condition doesn't match what SharePoint reports. Open the trigger in the designer, pick the
   operator's folder in its picker, and compare Code view with the generated `folderPath`; then read `{Path}` in a
   run of a test flow, or upload a heartbeat file in the browser. Correct the definition and record it in rows 3,
   20 or 22.

The other operators' copies are checked when they connect: [TESTING.md](../../TESTING.md) §4.

A failed run is your next fix. Call `diagnose_run` on it. Parse JSON failures, wrong list names and push
parameters each have a row in `flows/README.md` "Verify on import".

Mark step 05 `done`.
