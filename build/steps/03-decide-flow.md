# Step 03: the FleetDecide flow

**Who:** you. The operator approves the OneDrive for Business and Office 365 Users connections.
**Produces:** `FleetDecide`, turned on. The app calls it to send a decision or a reply (a prompt). It writes
`inbox/<kind>-<nonce>.json` into the bridge folder and the `FleetDecisions` row, and answers
`{ok, nonce, inboxFile, error}`.

## 1. Generate

```
python build/prepare.py flows
```

This writes `build/out/FleetDecide.json` from `flows/FleetDecide.definition.json`. It also says that
`FleetOutboxToLists` waits for step 04's app id and step 05's folder id; that is expected here. The script changes
three things and nothing else:

- it removes the review notes;
- it replaces the solution environment variables with `siteUrl` and `inboxFolderPath`;
- it removes `authentication` from the action inputs.

## 2. Connections

`connectors` in the file says which connection each connector needs:

| Connector | Mode | Connection |
| --- | --- | --- |
| `shared_sharepointonline` | `Embedded` | reuse step 02's |
| `shared_onedriveforbusiness` | `Embedded` | `pick_or_create_connection`; the operator approves. It must be the account whose OneDrive syncs the bridge folder |
| `shared_office365users` | `Invoker` | `pick_or_create_connection` |

`Invoker` is **Provided by run-only user**. It makes `by` in every inbox file the UPN of whoever runs the app,
taken from their own profile. The laptop checks that UPN against `fleet.mobile.operator`, so it must never be
changed to `Embedded`.

Fill `connectionRefsTemplate` with the three connection names and keep each `source` as given.

## 3. Create and turn on

1. Call `preflight_flow` with the definition and references. Fix only what it reports, in
   `flows/FleetDecide.definition.json` (a tracked fix). Add the row number from `flows/README.md` "Verify on
   import" to the fix, and record what you found in that row.
2. Call `list_flows`. If `FleetDecide` exists, call `update_flow`. Otherwise call `create_flow` with name
   `FleetDecide`.
3. Call `publish_flow`.

**Do not test it with `run_flow`.** An API call cannot supply the invoker's Office 365 Users connection (FlowAgent
reports `InvokerConnectionOverrideFailed`), and a passing run would write a real inbox file. The app tests it in
step 07.

**Check:** `get_flow` shows the flow on, with:

- trigger `manual` of kind `PowerAppV2`, with ten inputs in the order Kind, ApprovalId, Repo, Decision, Reason,
  Message, AnswersJson, Digest, ExpiresSeconds, Device;
- the `shared_office365users` reference in mode `Invoker`.

`tests/test_contract.py` holds the same input order on the repository side. Record the flow id under
`flows.FleetDecide` and mark step 03 `done`.
