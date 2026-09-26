# FleetAgent source notes: what to check in Studio

Every decision below was taken where the research (`research_notes/Mobile fleet scope/`) or the
Microsoft Learn pages read on 2026-09-26 left something unverified. Each one is a thing to confirm in
Power Apps Studio on the first paste, in the order the build sheet (`mobile/README.md`) pastes.
Nothing here changes the contract with the flows or the laptop bridge.

1. **No `@version` suffix on any control.** The schema makes the suffix optional and Learn says the
   current version is used when it is absent, but Studio's own code view always prints one and the
   compiler insists every instance of a type carries the same one. If a paste is refused for a
   version, copy the `Control:` value from Studio's code view for that type (for example
   `ModernText@1.0.0`) onto every instance of the type, and nowhere else.
2. **`TabIndex` only on the classic controls** (every `Gallery` has `=0`, the hidden `Timer` has
   `=-1`). Learn's modern Button page lists `AcceptsFocus` as removed ("always accepts keyboard
   focus") and no modern page lists `TabIndex`, so setting it there risks "Unknown property". Run the
   Accessibility checker on every screen; it must show 0 errors and 0 warnings.
3. **`Font` on the payload text is a CSS family list**, `="Consolas, 'Courier New', monospace"`.
   Learn says `Font` is "the name of the font family"; the theme YAML documents the CSS list form for
   its own `Font`, so the list is the best documented guess. If the control shows a proportional font,
   fall back to `="Courier New"`.
4. **The attention list sorts by `NeedsHuman` then by `At`, both descending**, not by `AgeSeconds`
   ascending. `AgeSeconds` is a text column and text sorts lexically ("120" before "95"); `At` is the
   same ordering in ISO-UTC text, which does sort chronologically and is delegable. Learn confirms
   `SortByColumns` on Text delegates to SharePoint but does not say whether a two-column sort does;
   if the formula shows a delegation warning, drop the second column and keep `"NeedsHuman"`.
5. **History is `Status = "approved" || ... || "sent"`, not `Status <> "pending"`**: `<>` on a text
   column does not delegate to SharePoint, `=` joined by `Or` does.
6. **`CountRows` does not delegate to SharePoint** (`PendingCount`, `NeedsYouCount`, the empty
   states): the counts are exact up to the data row limit (500). A fleet has tens of rows, not
   hundreds; leave the limit alone.
7. **Questions are rendered from `ParseJSON`** with `Table(ParseJSON(...))` and `Text(ThisItem.Value.q)`
   (Learn's documented dynamic-value pattern). `'default'` is written as a quoted identifier because
   it may be a reserved word. Invalid JSON in `QuestionsJson` shows as an error on that gallery only;
   answers stay free text on `ReplyScreen` (the flow's `AnswersJson` input is left empty by the app).
8. **`DateTimeValue` on the contract's `YYYY-MM-DDTHH:MM:SSZ` text.** Learn documents ISO 8601
   input for dynamic values and `Z` on output; check once on a phone that `Expires` and the heartbeat
   age read as UTC (a one-hour drift means the `Z` was ignored).
9. **`LaptopStale` uses `Now()` inside a named formula.** Named formulas recalculate when their
   inputs change, and the heartbeat row is refreshed every 60 s by `tmrRefresh`; confirm the banner
   appears within two minutes of stopping the laptop bridge. If it does not, the check belongs on the
   banner's own `Visible` formula rather than in `App.Formulas`.
10. **Row taps.** A control nested in a container inside a gallery cannot reach the gallery with
    `Select(Parent)` (its parent is the container; `Parent.Parent` is unsupported per Learn), so
    every text in a row carries the same two-line `OnSelect` as the gallery and the chevron button.
    Verify a tap anywhere on a row opens it on a phone.
11. **`Refresh` on five lists runs sequentially** in the header, the timer and Settings; Learn
    recommends `Concurrent` only for independent lookups and warns about many data sources at once.
    Wrap them in `Concurrent(...)` only if the refresh is visibly slow.
12. **Timers run only in Preview** inside Studio; `tmrRefresh` proves itself in the published app.
13. **`AutoHeight` is unsupported in horizontal containers**, so `KeyValueRow` instances set their
    own `Height` when `Wrap` is true (96 for a summary, 120 for `Says`). The payload text is the one
    `AutoHeight` label, inside a vertical scrolling container with `FillPortions: =0`, as Learn asks.
14. **Component instances inside AutoLayout containers take `FillPortions` and `Width` like any
    control.** Not seen compiled; if Studio ignores them, wrap each instance in a fixed-height container.
15. **Events are raised as `FleetHeader.OnBack()`** inside the component and handled on the
    instance as ordinary formulas (`OnBack: =If(!Back(), Navigate(HomeScreen, ...))`); unused events
    are set to `=false`. How Studio serialises an instance's event formula was not observed; if the
    paste complains, set them in the property pane once and copy what code view then shows.
16. **`ScreenSize` comparisons use `>=`** (`App.ActiveScreen.Size >= ScreenSize.Large`), the form
    Learn's responsive-layout page uses.
17. **`ModernIcon` uses `IconColor`**, not `Color`, and decorative icons have no `AccessibleLabel`
    so screen readers skip them (Learn's own advice).
18. **The theme YAML is comment-free**; Learn does not say whether the Themes pane accepts comments.
    Provenance: `BasePaletteColor` `#58A6FF` is the accent of the `dark` palette in
    `agentdata/theme.py` (the desk page's own neutral palette). The repository's default palette,
    `none`, keeps the terminal's colours and has no accent to take.
19. **`App.Theme.Colors.Primary` is decorative only** (the 3 px strip under each header). At
    2.5:1 against white it fails text contrast, so every text colour is a neutral RGBA; the measured
    pairs are in `mobile/README.md`.
20. **The History tab shows decided approvals** (`FleetApprovals`, the specification's source); a
    reply's outcome lives in `FleetDecisions` and is shown on `AgentScreen` as "Last reply"
    (`First(SortByColumns(Filter(FleetDecisions, Repo = ...), "Issued", Descending))`).
21. **`Reset(txtReason)` and `Set(busy, false)` run in `OnVisible`** of the two sending screens so a
    second visit starts clean and `busy` has a Boolean type before the first tap.
22. **`FleetDecide.Run` returns `{ok, nonce, inboxFile, error}`**: the flow's "Respond to a Power
    App" must declare `ok` as Yes/No and the other three as Text, or `r.ok` will not type-check.
23. **Data source names are the list display names** as Studio shows them after Add data. If a list
    was created with a different display name, rename it in SharePoint rather than editing formulas.
24. **`Host.OSType` is passed as the flow's `Device`** for the laptop's record only; no formula
    branches on it (Learn: do not use it to change behaviour).
25. **The Text control has no `Live` or `Role`** (Label-only properties), so results are announced
    with `Notify()` and no live region exists; the checker's "one Heading1 per screen" tip cannot be
    satisfied with modern controls and is expected.
26. **The official schema's `CodeComponent-ComponentName` regex has an unbalanced parenthesis**,
    which Python's `re` rejects; the local Draft 7 validation therefore skips the meta-schema check.
    The app has no PCF control, so the pattern is never evaluated. The copy stays unmodified.
