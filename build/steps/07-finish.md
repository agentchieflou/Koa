# Step 07: publish, mirror, hand over

**Who:** the operator publishes and opens the app on the phone; you verify and leave the repository matching what
Studio holds.
**Produces:** a published FleetAgent, `powerapp/src` mirroring Studio, and the first round trip ready to run.

## 1. Theme, publish, phone (operator)

Send this:

> Last clicks, about three minutes:
>
> 1. *(Optional; the app works with the default theme.)* **Themes** (the brush icon) > **Add a theme** > **Paste
>    theme** > paste everything below > select **FleetTheme**.
> 2. **Save**, then **Publish** > **Publish this version**.
> 3. On the phone, install **Power Apps** from the store, sign in with the same account, and open **FleetAgent**
>    once. Pushes reach only someone who has opened the app in the last 30 days.

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

1. `get_run_history` for `FleetOutboxToLists` shows Succeeded runs since step 05, and the latest heartbeat run is
   less than 15 minutes old.
2. Ask the operator to open the app (the play link below) and check four things:
   - **Settings** shows them as signed in;
   - the laptop's operator matches them, with no mismatch banner;
   - the heartbeat is recent, with no "not syncing" banner;
   - **Home > Attention** lists the laptop's repositories.

## 4. Hand over

Commit only the tracked changes: `powerapp/`, `flows/`, `build/prepare.py`, and the rows in `powerapp/NOTES.md`
and `flows/README.md`. Use a Conventional Commit message such as
`fix(app): what Studio's first compile required`. Never commit `build/out/` or `build/fleet.config.json`. If you
cannot push, leave the commit for the operator to push.

Then report:

- **Play link:** `https://apps.powerapps.com/play/e/<environment>/a/<appId>`
- **Studio:** `studioUrl`
- **Flows:** `FleetDecide` and `FleetOutboxToLists`, both on, with their ids
- **Lists:** the five, on `siteUrl`
- **Fixes:** every fix made and where it is recorded
- **Next:** `TESTING.md` §3. Send a prompt from the phone's Reply screen and watch it reach the agent

Mark step 07 `done`.
