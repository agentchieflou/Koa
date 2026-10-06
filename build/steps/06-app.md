# Step 06: the app

**Who:** the operator adds the data sources and pastes the app into Studio; you put each paste on their clipboard,
read the errors Studio shows, and fix them in the repository.
**Produces:** in the open Studio session, the six screens, three components and the App object of
`powerapp/src`, with no errors in the App checker.

The sources are final. Studio's code view pastes a whole component or screen from its `.pa.yaml` file (generally
available since March 2025); the App object cannot be pasted, so its four properties are pasted into the formula
bar instead. This is the root `README.md`'s Studio build sheet, steps 3 to 7, with you beside the operator.

## 1. The data sources (operator)

No file can carry a data source or a connection; they are added in Studio. Send this:

> In the FleetAgent tab in Studio, please add the data. About two minutes:
>
> 1. **Data** (the cylinder icon on the left) > **Add data** > search **SharePoint** > pick your connection > choose
>    the site `<siteUrl>` > tick **FleetAttention**, **FleetApprovals**, **FleetDecisions**, **FleetNotifications**
>    and **FleetHeartbeat** > **Connect**.
> 2. The **Power Automate** icon on the left (or **...** > **Power Automate**) > **Add flow** > **FleetDecide**.
>
> Reply with the names the Data pane shows, exactly as written there, and say whether FleetDecide is listed under
> Power Automate.

Mark the step `waiting` until they reply.

**Check:** the five names read exactly `FleetAttention`, `FleetApprovals`, `FleetDecisions`, `FleetNotifications`
and `FleetHeartbeat`. A name with a suffix (`FleetAttention_1`) means the list was added twice: ask the operator to
remove the extra one in the Data pane. If `FleetDecide` is missing, step 03's flow is off or in another environment.

## 2. Paste the app (operator, with you)

```
python build/prepare.py paste
```

lists the thirteen pastes in order and writes each one to `build/out/paste/`: the three components, the six screens
in the order that leaves the fewest names unresolved, then the App object's four properties. For each paste, run

```
python build/prepare.py paste <N>
```

which puts paste N on the Windows clipboard (or, if it cannot, names the file to open and copy) and prints where it
goes. Tell the operator in one line what to do with it, from what the command printed, for example:

> Paste 4 of 13, SettingsScreen, is on your clipboard. In Studio: Tree view > Screens tab > right-click the empty
> area > Paste code. Reply "done", or paste me the message if Studio refuses it.

Go one paste at a time. Expect `name isn't recognized` on screens not pasted yet while you go; they clear when the
last screen and the App's `Formulas` are in. Once `HomeScreen` is in, ask the operator to delete `Screen1`
(right-click > **Delete**) and save (Ctrl+S).

## 3. Clear the errors

After the last paste, ask the operator:

> Please open the **App checker** (the stethoscope icon at the top right), expand **Formulas** and every other
> section that shows a number, and paste me every line, with the control and property each one names.

Fix each in this order:

1. a paste Studio refused (its message, against the root `README.md` step 10 table);
2. control version conflicts;
3. duplicate names;
4. unknown properties;
5. App properties;
6. the rest.

**Make every fix in `powerapp/src`, the repository's copy,** then run `python build/prepare.py paste` again and
have the operator replace just what changed: delete that component or screen and paste it again, or paste the App
property again. The repository stays the source, and its tests keep checking each fix. These are the only fixes
allowed:

| Studio says | Fix |
| --- | --- |
| a control's version, or "template-version conflict" | ask the operator to right-click any control of that type > **View code** and paste you its `Control:` line; put that exact value on **every** instance of the type in every file (`powerapp/NOTES.md` item 1) |
| `Unknown property 'X'` | ask for **View code** on that control and the list of properties Studio offers for it; rename `X` to the property it shows for the same purpose (for example a `Font` form, `powerapp/NOTES.md`). Keep the formula |
| an enum name or member | ask for **View code** on a control that uses it and copy the form Studio prints, verbatim |
| `name isn't recognized` on a list or `FleetDecide` | not a code fix: the data source is missing or misnamed; go back to section 1 |
| `name isn't recognized` on a screen or a component | that paste has not been done yet, or was refused; redo it |
| a type error on `Created` | already handled with `Text(...)`; report any that remains |
| anything else | the smallest edit that clears it, without removing a control, a formula or a check. If clearing it needs a design change, stop and ask the operator, quoting the message |

After each round, run `python -m pytest -q`. A fix that breaks a test is the wrong fix.

Record every fix in `powerapp/NOTES.md`: the item it settles, the message, and the change. If the same message
survives two fixes, mark the step `blocked` with the message text.

**Check:**

- the operator reports the App checker shows no errors;
- the tree view's Screens tab shows `HomeScreen`, `AgentScreen`, `ApprovalScreen`, `DecideScreen`,
  `ReplyScreen` and `SettingsScreen` and no `Screen1`, and its Components tab shows `EmptyState`, `KeyValueRow`
  and `FleetHeader`;
- `python -m pytest -q` passes.

Mark step 06 `done`, listing the fixes made.
