# Koa

Mobile Fleet - Knees of Ants: the phone and tablet side of the fleet. **FleetAgent**, a Power Apps canvas
app, the Power Automate flows that carry records between each operator's laptop and five SharePoint
lists, and the workbook that creates those lists. Several operators share one site; each sees their own
fleet, and the team's read-only.

Imported from this-next-please@913d157765ef8a7944d21a8167b15771edfd133f (`mobile/` and
`tests/test_mobile_powerapp.py`, history kept; this-next-please#600). The laptop side, the bridge
(`ad-fleet mobile ...`), stays in this-next-please; the two meet only at the contract pinned in
`contract/`. Nothing here imports the laptop's Python package.

Koa also holds the **Data Czars SharePoint site** (`site/`), the home of data-czars and the tooling it supports in
the PAE: its design, its lists and their formatting, a sheet per page with the Copilot prompt that builds it, the
intake to Jira, the usage reports' landing, the site's Copilot skill and its three agents, and the prompts that scan
data-czars, usage_tool and the fleet for the facts the pages need (they stay on your machine). Start at
[site/README.md](site/README.md).

To run the first round trip (a prompt typed on the phone reaching an agent on the laptop), follow
[TESTING.md](TESTING.md).

## The mobile lane: FleetAgent

The laptop's fleet bridge (`ad-fleet mobile init`, then the bridge loop) writes an outbox of small
JSON records into the operator's own folder of the site's `FleetAgent` library, synced to the laptop as a
OneDrive shortcut: one attention row per repository, a mirror of every approval request, every
notification, and a heartbeat. Power Automate flows (one copy per operator) move those records into five
SharePoint lists, each row stamped with its `Operator`, and send a push to that operator. **FleetAgent**, the canvas app in `powerapp/`, shows those rows on
a phone or a tablet and carries the operator's decision or reply back through one flow, which writes
a file into the sender's own bridge inbox. The laptop applies it only after checking the digest, the operator's
identity and the expiry. The app decides nothing: every state, colour and sentence on its screens is
the laptop's own word, and the only rule of its own is "three missed heartbeats means not syncing".

```
README.md                    this build sheet
build/                       the Copilot build: README (the operator's part), steps/01-07 (the agent's), prepare.py
.github/skills/              build-fleetagent (runs build/) and build-czars-site (site/'s lists), skills a Copilot agent loads
.github/prompts/             czars-scan-*: read data-czars, usage_tool and the fleet into site/local/ (never committed)
site/                        the Data Czars SharePoint site: design, lists, page sheets, intake, skill, agents (site/README.md)
TESTING.md                   the first round trips: a reply (a prompt) and an approval, phone to laptop
AGENTS.md                    for coding agents working in this repository
contract/
  PIN                        the pinned tag, its source commit and the sha256 of every file below
  fleet-mobile.v1.schema.json  the laptop's records, the inbox records, the five lists, FleetDecide's signature
  examples/*.json            one record per kind, the Parse JSON samples
powerapp/
  NOTES.md                   every decision taken where the research left something unverified
  src/                       the app, one entity per file, exactly as Studio lays sources out
    App.pa.yaml              StartScreen, BackEnabled, OnError, Formulas (typed by hand, step 6)
    _EditorState.pa.yaml     screen and component order
    Screens/*.pa.yaml        HomeScreen, AgentScreen, ApprovalScreen, DecideScreen, ReplyScreen, SettingsScreen
    Components/*.pa.yaml     EmptyState, KeyValueRow, FleetHeader
  themes/FleetTheme.yaml     the theme to paste in the Themes pane
  sample/*.json              three to five rows per list, to seed a first look
  schema/                    the official v3.0 schema (unmodified) and its licence note
flows/                       FleetOutboxToLists and FleetDecide, their build and import sheets
data/                        FleetAgent.xlsx, the list source and Excel fallback, and its generator
tests/
  test_mobile_powerapp.py    the guard over powerapp/
  test_contract.py           the pin, the examples, the lists, FleetDecide and the workbook against the contract
  test_flows.py              every Parse JSON schema in the flows against every pinned example
  test_site.py               the site: its lists and site scripts, formatters, flow, navigation, page sheets, artwork
```

The list columns, the flow signature and the deep-link parameters are the shared contract (v1) the
flows author and the laptop bridge build to: `contract/fleet-mobile.v1.schema.json`, pinned by
`contract/PIN`. The columns are also listed in `tests/test_mobile_powerapp.py` (and held equal to
the contract by `tests/test_contract.py`), and the lists themselves are created by `data/README.md`.

## The Studio build sheet

**The quickest way is the Copilot build, [build/README.md](build/README.md).** A GitHub Copilot agent
walks you through this same sheet: it writes the list flow and both flows as packages you import, puts
each paste below on your clipboard in order, reads back the run reports and Studio's errors, and fixes
the sources. It uses no MCP server and no agent plugin, which this organisation blocks; every click is
yours, in the browser. The sheet below is the same work without the agent.

Everything below is done once, by hand, in Power Apps Studio. Nothing in this folder is imported as
a file: whole screens are pasted through Code view (GA since March 2025), the App object is typed
into the formula bar, and data sources and display settings are Studio-side settings the YAML cannot
carry.

1. **Create the five lists** on the SharePoint site the flows write to: `FleetAttention`,
   `FleetApprovals`, `FleetDecisions`, `FleetNotifications`, `FleetHeartbeat`, with the columns in
   `data/README.md`. Every column is text (single line unless the sheet says multi-line) and
   `Operator` with `Title` is the key. Lock all five to the site's Owners (`data/README.md` §Owners
   only). To seed a first look, load the rows in `powerapp/sample/*.json`; replace
   `operator@example.com` (the heartbeat's `Title` and every `Operator`) with your own UPN, or the
   app shows you nothing under *My fleet* and warns about a mismatch (which is itself a fair first test
   of the banner).
2. **Create the app.** Power Apps > Create > Blank app > Blank canvas app, name `FleetAgent`,
   format **Tablet**. Then Settings:
   - Updates > New: **Modern controls and themes** on; **Enhanced component properties** on.
   - Display: **Scale to fit OFF**, **Lock aspect ratio OFF**, **Lock orientation OFF**, Apply.
     Reason: these three are not in the YAML (the schema has no slot for them) and the screens are
     written as responsive containers that only behave with all three off; Microsoft's own guidance
     for one app on phone, tablet and web is a Tablet app with exactly these settings.
   - General: leave the data row limit at 500.
3. **Add data.** Data > Add data > SharePoint > your site > tick the five lists. Their names in the
   Data pane must read exactly `FleetAttention` and so on; every formula names them that way. Then
   the Power Automate pane > Add flow > `FleetDecide` (the Power Apps (V2) flow the flows author
   built; inputs `Kind, ApprovalId, Repo, Decision, Reason, Message, AnswersJson, Digest` as text,
   `ExpiresSeconds` as number, `Device` as text; it responds with `ok` (Yes/No), `nonce`, `inboxFile`,
   `error`).
4. **Theme.** Themes pane > Add a theme > Paste theme > paste the whole of `powerapp/themes/FleetTheme.yaml`
   > select `FleetTheme`. The seed colour `#58A6FF` is the accent of the desk's `dark` palette in
   this-next-please's `agentdata/theme.py`; the app uses `App.Theme.Colors.Primary` only for the
   thin strip under each header, and neutral colours for all text (see Contrast below).
5. **Paste, in this order** (each file is one paste; the order makes every reference resolve):
   1. Components, through the Components tab of the tree view: right-click > Paste code, one file
      each, in the order `Components/EmptyState.pa.yaml`, `Components/KeyValueRow.pa.yaml`,
      `Components/FleetHeader.pa.yaml`.
   2. Screens, through the Screens tab: `SettingsScreen`, `ReplyScreen`, `DecideScreen`,
      `ApprovalScreen`, `AgentScreen`, `HomeScreen`. This is the order that leaves the fewest names
      unresolved at each step: a formula that names a screen not yet pasted shows "name isn't
      recognized" until that screen exists (every back button names `HomeScreen`, so a few of those
      are unavoidable), and `HomeScreen` last clears them all.
   A pasted screen arrives beside the default `Screen1`; once `HomeScreen` is in, delete `Screen1`.
   If a paste is refused, read the message against the triage table in step 10 before changing a
   line. Paste a whole file each time; a partial paste leaves the screen half built.
6. **The App object, by hand.** Code view cannot paste the App object. Select App in the tree view
   and copy each property from `powerapp/src/App.pa.yaml` into the formula bar, without the leading
   `=`: `StartScreen`, `BackEnabled`, `OnError`, and `Formulas` (the whole block, comments included).
   Do this after the screens exist, because `StartScreen` names three of them. Leave `OnStart` empty.
7. **Version suffixes.** The sources omit every `@version` on purpose. If Studio insists on one for
   a type ("template-version conflict" or "must reference the same version"), open code view on any
   control of that type, read the exact `Control:` value it prints, and put that value on every
   instance of the type across all files. Never invent a version and never mix two for one type.
8. **Save, publish, share** the app with every operator (as User; decline sharing the lists, which
   stay Owners-only), then open it once in Power Apps mobile on the phone: push notifications reach only a user who has opened the app in the last 30 days.
9. **Test checklist.** Use the preview device picker at 390x844, 844x390, 820x1180 and 1180x820
   after publishing (the authoring canvas does not reflow), and then a real phone in both orientations:
   - Home: the tabs switch the four lists; a row tap opens the agent or the approval; on widths of
     900 px and more the right pane shows the selected repository instead of navigating.
   - The banner appears when the laptop bridge is stopped for more than three heartbeats and when
     you sign in as an account other than the laptop's operator.
   - Approval: Approve and Deny are disabled once the row is decided or past its expiry; Deny needs
     a reason before Send is enabled; a sent decision shows the flow's `error` verbatim when it fails.
   - Reply: disabled with the laptop's sentence when the session is external.
   - *Show the team's* on Home lists the sample's `colleague@example.com` row, and Approve, Deny
     and Reply are disabled on it, naming whose it is.
   - Deep links: a push with `screen=approval&approvalId=<id>` opens the approval; with
     `screen=agent&repo=<alias>` the agent. Parameters are read at launch only; a link into an app
     that is already open needs `restartApp=true` (see `research_notes/Mobile fleet scope/notifications_intune_powerapps.md`).
   - Accessibility checker: 0 errors and 0 warnings on every screen; every button is at least 48 px.
   - Rotate the phone: nothing is clipped and no screen scrolls sideways.
10. **Troubleshooting.** The parse errors Studio reports on a paste, and what each one means:

    | Studio says | Cause | Fix |
    | --- | --- | --- |
    | `Power Fx expressions must start with '='` | a property value without `=` | every value starts with `=` |
    | `mapping values are not allowed` / a formula cut at a colon | `: ` inside a plain single-line formula | single-quote the value or make it a `\|-` block |
    | `Expected 'MappingEnd', got 'Scalar'` | wrong indentation | two spaces per level, exactly as in the file |
    | a control silently missing | a `Children:` item without the leading `- ` | every child is `- Name:` |
    | `Named object value cannot be null` | an empty `Properties:` | remove it or give it a property |
    | duplicate key error | the same property or control name twice | rename |
    | a multi-line quoted string error | a quoted formula spanning lines | use a `\|-` block |
    | `found character that cannot start any token` | a tab character | spaces only |
    | template-version conflict | two versions for one control type | step 7 |
    | `name isn't recognized` on `FleetAttention` etc. | a data source not yet added | step 3, then paste again |
    | `name isn't recognized` on `FleetDecide.Run` | the flow is not added to the app | Power Automate pane, step 3 |
    | `name isn't recognized` on `AgentScreen` or `HomeScreen` | that screen is not pasted yet | finish step 5; the error clears when the screen exists |

    `powerapp/NOTES.md` lists every place where the research could not verify a property form; if a
    paste fails on one of those lines, that list says what to try.

## Other ways in

- **`pac canvas pack --layout SourceCode`** builds an `.msapp` from a `Src/*.pa.yaml` tree offline
  (`pac canvas pack --sources <dir> --msapp FleetAgent.msapp --layout SourceCode`), which Studio then
  opens with File > Open > Browse. The `pack`/`unpack` commands are deprecated in favour of Git
  integration, and whether they accept a hand-authored tree that was never unpacked is unverified.
- **The Canvas Authoring MCP server and Microsoft's `canvas-apps` and `power-automate` plugins** would
  push the `.pa.yaml` files into a live coauthoring session and create the flows directly. This
  organisation blocks MCP servers and agent plugins, so nothing here uses them: the Copilot build
  pastes through code view and imports packages instead (`build/README.md`).

## Contrast

Every text colour in the app is a neutral RGBA chosen against the fill it sits on, measured with
this-next-please's `agentdata.theme.contrast_ratio`:

| Text | On | Ratio |
| --- | --- | --- |
| body `#242424` | screen `#FAFAFA` | 14.9:1 |
| body `#242424` | card `#FFFFFF` | 15.5:1 |
| muted `#616161` | screen `#FAFAFA` | 5.9:1 |
| muted `#616161` | card `#FFFFFF` | 6.2:1 |
| banner `#242424` | banner `#FFF4CE` | 14.1:1 |
| payload `#242424` | payload surface `#F3F2F1` | 13.9:1 |

`App.Theme.Colors.Primary` (seed `#58A6FF`) is 2.5:1 against white, so it is never used for text.
Badges, buttons and the tab list take their colours from the theme's accessible ramp; status is
always carried by the word on the badge, never by its colour alone.

## Checking the sources without Studio

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

holds the sources to the schema's shape and to the app's ground rules, and the lists, the flows and
the workbook to the pinned contract. CI runs the same on Ubuntu and on Windows with
`core.autocrlf=true`. The full
Draft 7 validation against `powerapp/schema/pa.schema.yaml` needs `jsonschema` (in `requirements-dev.txt`):
merge every `src/**/*.pa.yaml` into one document, as the schema says all files are logically
combined, and validate it with `jsonschema.Draft7Validator(schema).iter_errors(merged)`; skip
`check_schema`, because the official schema's PCF-name regex does not compile under Python's `re`
(NOTES.md, item 26).
