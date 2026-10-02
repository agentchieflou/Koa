# Step 06: the app

**Who:** the operator adds the data sources; you push the app and make it compile.
**Produces:** in the open Studio session, the six screens, three components and the App object of
`powerapp/src`, compiling with zero errors.

The sources are final. **Do not use the canvas-apps plugin's `/canvas-app` create workflow, its planner or its
screen builders.** They design a new app from a description; this app is already designed, reviewed and tested.
Use the MCP server's own tools directly: `sync_canvas`, `compile_canvas`, `describe_control`,
`list_data_sources`, `get_data_source_schema`, `list_apis` and `describe_api`.

## 1. The data sources (operator)

The plugin's `add-data-source` skill says it plainly: a coding agent cannot add data sources or connections; they
are added in Studio. Send this:

> In the FleetAgent tab in Studio, please add the data. About two minutes:
>
> 1. **Data** (the cylinder icon on the left) > **Add data** > search **SharePoint** > pick your connection > choose
>    the site `<siteUrl>` > tick **FleetAttention**, **FleetApprovals**, **FleetDecisions**, **FleetNotifications**
>    and **FleetHeartbeat** > **Connect**.
> 2. The **Power Automate** icon on the left (or **...** > **Power Automate**) > **Add flow** > **FleetDecide**.
>
> Reply here when the five lists and the flow show in the Data pane.

Mark the step `waiting` until they reply.

## 2. Verify the data sources

1. Call `list_data_sources`. The five names must read exactly `FleetAttention`, `FleetApprovals`,
   `FleetDecisions`, `FleetNotifications` and `FleetHeartbeat`. A name with a suffix (`FleetAttention_1`) means
   the list was added twice: ask the operator to remove the extra one in the Data pane.
2. Call `get_data_source_schema` for each list. Every column the contract names must be there
   (`contract/fleet-mobile.v1.schema.json` `$defs/<List>/properties`). The one exception is
   `FleetApprovals.Created`, which is SharePoint's own Date and Time column.
3. Call `list_apis`, then `describe_api` for `FleetDecide`. `Run` must take the ten inputs in this order: Kind,
   ApprovalId, Repo, Decision, Reason, Message, AnswersJson, Digest, ExpiresSeconds, Device. The app passes them by
   position. If the order differs, stop: step 03's flow is not the repository's.

## 3. Push the sources

1. Make an empty working directory, `build/out/canvas/FleetAgent`, and take its **absolute** path. It must hold
   nothing but `.pa.yaml` files; `build/out/` is git-ignored. Never use the repository root.
2. Call `sync_canvas` with that path. It now holds the blank app: `App.pa.yaml`, `Screen1.pa.yaml` and
   `_EditorState.pa.yaml`.
3. Run `python build/prepare.py canvas-in <absolute path>`. It does three things:
   - copies `App.pa.yaml` and `_EditorState.pa.yaml`;
   - copies every `powerapp/src/Screens/*.pa.yaml` to the directory's root and `powerapp/src/Components/*` to
     its `Components/`, the layout the MCP server uses;
   - removes the blank `Screen1.pa.yaml`.
4. Call `compile_canvas` with the same path.

## 4. Make it compile

Work on the diagnostics in the plugin's order (its `references/ValidationWorkflow.md`):

1. YAML parse errors;
2. control version conflicts;
3. duplicate names;
4. unknown properties;
5. App properties;
6. the rest.

**Make every fix in `powerapp/src`, the repository's copy,** then rerun `canvas-in` and `compile_canvas`. The
repository stays the source, and its tests keep checking each fix. These are the only fixes allowed:

| Diagnostic | Fix |
| --- | --- |
| a control's version, or "template-version conflict" | `describe_control` for that type; copy its exact `Control:` value onto **every** instance of the type in every file (`powerapp/NOTES.md` item 1) |
| `Unknown property 'X'` | `describe_control`; rename `X` to the property it lists for the same purpose (for example a `Font` form, `powerapp/NOTES.md`). Keep the formula |
| an enum name or member | copy the `Enum name:` line from `describe_control` verbatim |
| `Name isn't recognized` on a list or `FleetDecide` | not a code fix: the data source is missing or misnamed; go back to section 2 |
| `Name isn't recognized` on a screen | a screen file was not copied; rerun `canvas-in` |
| a type error on `Created` | already handled with `Text(...)`; report any that remains |
| anything else | the smallest edit that clears it, without removing a control, a formula or a check. If clearing it needs a design change, stop and ask the operator, quoting the diagnostic |

After each round, run `python -m pytest -q`. A fix that breaks a test is the wrong fix.

Record every fix in `powerapp/NOTES.md`: the item it settles, the diagnostic, and the change. If the same
diagnostic survives two fixes, mark the step `blocked` with the diagnostic text.

## 5. Check that the app round-trips

`compile_canvas` succeeding proves the YAML is valid. It does not prove the app reached Studio.

1. Make a second empty directory, `build/out/canvas/verify-1`, and call `sync_canvas` into it.
2. It must hold all six screens and all three components, each with its controls, and an `App.pa.yaml` with the
   `Formulas` block.
3. If `Screen1` is still there, ask the operator to right-click **Screen1** in the tree view, choose **Delete**,
   and save. Then sync again into `verify-2`.

**Check:**

- the last compile shows zero errors;
- the verify sync holds `HomeScreen`, `AgentScreen`, `ApprovalScreen`, `DecideScreen`, `ReplyScreen`,
  `SettingsScreen`, `EmptyState`, `KeyValueRow` and `FleetHeader`;
- `python -m pytest -q` passes.

Mark step 06 `done`, listing the fixes made.
