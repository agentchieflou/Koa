# Step 07: publish, mirror, hand over

**Who:** the operator publishes and opens the app on the phone; you verify and leave the repository matching what
Studio holds.
**Produces:** a published FleetAgent, `powerapp/src` mirroring Studio, and the first round trip ready to run.

## 1. Theme, publish, phone (operator)

Send this:

> Last clicks, about five minutes:
>
> 1. *(Optional; the app works with the default theme.)* **Themes** (the brush icon) > **Add a theme** > **Paste
>    theme** > paste everything below > select **FleetTheme**.
> 2. **Save**, then **Publish** > **Publish this version**.
> 3. **Share** (Power Apps > Apps > FleetAgent > **Share**): add every other operator as a **User**, not a
>    co-owner. If the dialog offers to give them access to the data, leave it: the lists stay readable by the
>    site's Owners only, and every operator is already one.
> 4. In Power Automate, open **FleetDecide** > **Run only users** > **Edit**: add every other operator, and keep
>    **Office 365 Users** on **Provided by run-only user** (SharePoint stays on your connection). Each operator's
>    phone then signs its messages with their own account.
> 5. Send each operator `build/each-operator.md`. Connecting their own laptop and phone takes them about five
>    minutes. Do it yourself first, if you haven't in step 05.

Paste the full content of `powerapp/themes/FleetTheme.yaml` under the message.

## 2. Mirror Studio back into the repository

Studio may have normalised what you pushed: version suffixes, property order, quoting. The repository should hold
what Studio holds, as long as the tests still pass.

1. Make an empty directory, `build/out/canvas/mirror`, call `sync_canvas` into it, then run
   `python build/prepare.py canvas-out <absolute path>`.
2. Run `python -m pytest -q`.
   - **Tests pass:** keep the changes. `git diff --stat powerapp/src` shows them.
   - **Tests fail:** run `git checkout -- powerapp/src` and record in `powerapp/NOTES.md` what Studio changes
     that the tests refuse, with the failing test names. That is a follow-up, not something to force through now.

## 3. Verify end to end

1. `get_run_history` for the building operator's `FleetOutboxToLists (<UPN>)` shows Succeeded runs since step 05,
   and the latest heartbeat run is less than 15 minutes old.
2. Ask the operator to open the app (the play link below) and check five things:
   - **Settings** shows them as signed in;
   - the laptop's operator matches them, with no mismatch banner;
   - the heartbeat is recent, with no "not syncing" banner;
   - **Home** says *Showing my fleet*, and **Attention** lists their own laptop's repositories;
   - *Show the team's* adds the other operators' rows once their laptops are connected, and Approve, Deny and
     Reply stay disabled on those rows.

## 4. Hand over

Commit only the tracked changes: `powerapp/`, `flows/`, `build/prepare.py`, and the rows in `powerapp/NOTES.md`
and `flows/README.md`. Use a Conventional Commit message such as
`fix(app): what Studio's first compile required`. Never commit `build/out/` or `build/fleet.config.json`. If you
cannot push, leave the commit for the operator to push.

Then report:

- **Play link:** `https://apps.powerapps.com/play/e/<environment>/a/<appId>`
- **Studio:** `studioUrl`
- **Flows:** `FleetDecide` and every `FleetOutboxToLists (<UPN>)`, all on, with their ids and owners
- **Lists:** the five, on `siteUrl`
- **Fixes:** every fix made and where it is recorded
- **Next:** `TESTING.md` §3. Send a prompt from the phone's Reply screen and watch it reach the agent

Mark step 07 `done`.
