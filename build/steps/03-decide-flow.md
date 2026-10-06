# Step 03: the FleetDecide flow

**Who:** you write the package; the operator imports it, picks the connections and turns it on.
**Produces:** `FleetDecide`, turned on: one flow for every operator. The app calls it to send a decision or a reply
(a prompt). It writes `<library>/<sender's UPN>/inbox/<kind>-<nonce>.json`, so each operator's message reaches their
own laptop and nobody else's, plus the `FleetDecisions` row, and answers `{ok, nonce, inboxFile, error}`.

## 1. Generate

```
python build/prepare.py flows
```

This writes `build/out/FleetDecide.zip` (the package to import) and `build/out/FleetDecide.json` (the same flow to
read) from `flows/FleetDecide.definition.json`. It also says that `FleetOutboxToLists` waits for step 04's app id;
that is expected here. The script changes three things and nothing else:

- it removes the review notes;
- it replaces the solution environment variables with `siteUrl` and `library`;
- it removes `authentication` from the action inputs.

## 2. Connections

`connectors` in the JSON says which connection each connector needs:

| Connector | Mode | Connection |
| --- | --- | --- |
| `shared_sharepointonline` | `Embedded` | the operator's own, the one step 02 used (a site Owner's, so it can write into every operator's folder) |
| `shared_office365users` | `Invoker` | the operator's own Office 365 Users connection; on every run it is replaced by the caller's |

`Invoker` is **Provided by run-only user**. It makes `by` in every inbox file the UPN of whoever runs the app, taken
from their own profile, and that same UPN picks the inbox folder. So a message can only land in its sender's own
folder, and the laptop checks the UPN again against `fleet.mobile.operator`. It must never be changed to the
operator's own connection.

## 3. Import and turn on (operator)

Send this:

> Please import FleetDecide. About three minutes:
>
> 1. https://make.powerautomate.com, environment **<environment>** > **My flows** > **Import** >
>    **Import Package (Legacy)** > **Upload** `<path>\build\out\FleetDecide.zip`.
> 2. The flow's **Import setup**: **Create as new**, or **Update** if a `FleetDecide` is already there > **Save**.
>    **SharePoint**: your connection > **Save**. **Office 365 Users**: your connection (or **+ Create new**) >
>    **Save**. Then **Import**, then **Open flow**.
> 3. **Turn on** (top bar) if it is off.
> 4. Back on the flow's page, **Run only users** > **Edit**. Check that **Office 365 Users** says **Provided by
>    run-only user** and **SharePoint** says your connection; change Office 365 Users to **Provided by run-only
>    user** if it does not. **Save**.
> 5. **Edit** the flow and open its trigger, **When Power Apps calls a flow (V2)**. Reply here with its inputs, top
>    to bottom, and what step 4 showed.

Mark the step `waiting` until they reply. If the import page refuses the package, take the exact message (row B1 in
`build/README.md`); the fallback is to build the flow by hand from `flows/README.md`.

**Do not ask for a test run.** A run needs a caller's Office 365 Users connection, and a passing run would write a
real inbox file. The app tests it in step 07.

**Check:**

- the inputs, in order: Kind, ApprovalId, Repo, Decision, Reason, Message, AnswersJson, Digest, ExpiresSeconds,
  Device (`tests/test_contract.py` holds the same order on the repository side);
- Office 365 Users is **Provided by run-only user** (row B2: record whether the import kept it or the operator had
  to set it);
- the flow is on.

If the import or the designer reports an error in the definition, fix it in `flows/FleetDecide.definition.json`
(a tracked fix), add it to the matching row of `flows/README.md` "Verify on import", regenerate, and have the
operator import again with **Update**.

Record `flows.FleetDecide` as `imported` and mark step 03 `done`.
