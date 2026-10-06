---
name: build-fleetagent
description: Builds the FleetAgent mobile app end to end on Microsoft 365 from this repository - the five SharePoint lists, the FleetDecide and FleetOutboxToLists flows, and the canvas app from powerapp/src - through the canvas-apps and power-automate plugins. Use when asked to build, set up, deploy, install, rebuild or continue building FleetAgent, the Power App, the mobile app, the lists or the flows.
---

# Build FleetAgent

You are deploying an app that is already designed. `powerapp/src`, `flows/` and `contract/` are finished,
reviewed sources: your job is to put them into the operator's tenant exactly as they are, and to fix only what a
validator rejects. Do not redesign a screen, rename a control, add a feature, or "improve" a formula.

## Before anything

1. Read `build/README.md` (what the operator does and what you do), then `.github/copilot-instructions.md`.
2. Read `build/out/state.json` if it exists. It records the steps already done and the values found. Resume at
   the first step not marked `done`. If the file does not exist, start at step 01.
3. Confirm that the MCP tools are present. The canvas server's tools are `connect`, `sync_canvas`,
   `compile_canvas`, `list_data_sources`, `list_apis`, `describe_control` and so on. FlowAgent's are
   `list_environments`, `create_flow`, `run_flow`, `pick_or_create_connection` and so on. Clients prefix them:
   `canvas-authoring-<tool>` and `flowagent-<tool>` in Copilot CLI, `mcp__canvas-authoring__<tool>` in Claude Code.
   If either set is missing, do step 01's plugin check and stop there.

## The steps

Do them in order. Do each one completely: run the step's **Check** and record the result in
`build/out/state.json` before you open the next file.

| Step | File | Who | Produces |
| --- | --- | --- | --- |
| 01 | `build/steps/01-prerequisites.md` | you; the operator signs in | tools checked, `build/fleet.config.json` filled (environment, siteUrl, library, operators) |
| 02 | `build/steps/02-lists.md` | you | the five lists with every column and index, the bridge library with one folder per operator, all six locked to the site's Owners |
| 03 | `build/steps/03-decide-flow.md` | you | `FleetDecide`, on |
| 04 | `build/steps/04-app-shell.md` | the operator, guided by you | a blank Tablet app with coauthoring on; `studioUrl`, `appId` |
| 05 | `build/steps/05-outbox-flow.md` | you; the operator changes owners | one `FleetOutboxToLists (<UPN>)` per operator, on, each reading only that operator's folder and owned by them |
| 06 | `build/steps/06-app.md` | the operator adds data; you push the app | every screen, component and the App object in Studio, compiling clean |
| 07 | `build/steps/07-finish.md` | the operator publishes and shares; you verify | a published app shared with every operator, the repository mirrored and tested, the first round trip ready |

## State file

Write `build/out/state.json` as `{"steps": {"01": {"status": "done", "at": "<UTC>", "notes": "..."}, ...},
"flows": {"FleetDecide": "<flow id>", ...}, "connections": {"shared_sharepointonline": "<connection name>", ...}}`.
`status` is one of `done`, `waiting` (on the operator; say for what) or `blocked` (say why). Never put a token,
password or secret in it.

## Rules for the whole build

- **The operator's clicks are theirs.** When a step says *Operator*, tell them exactly what to click, in the
  words of the step, and wait for their reply. Never try to work around a click that the plugins say no tool can
  make. That covers adding data sources, publishing, sharing, and the app's display settings.
- **Every write is idempotent.** Look before you create: an existing list, column, connection or flow with the
  name you want is reused, never duplicated. `create_flow` refuses a duplicate name; use `update_flow` on the
  existing id instead.
- **Two refusals in a row stop you.** If the same tool call fails twice with the same error, mark the step
  `blocked` with the tool, the arguments (without secrets), the error and what you tried, and tell the operator.
  Do not loop.
- **Fix what the validators say, and nothing else.** A compile or validation diagnostic is fixed in the smallest
  edit that clears it. Each fix is written into `powerapp/NOTES.md` (app) or `flows/README.md` "Verify on
  import" (flows), naming the diagnostic and the change. Run `python -m pytest -q` after every change to a
  tracked file.
- **Nothing tenant-specific in tracked files.** Site URLs, ids, UPNs and folder ids live in
  `build/fleet.config.json` and `build/out/`, which git ignores. The tests refuse them anywhere else.
- **Commit only the repository's own changes.** That means `powerapp/`, `flows/` and doc rows. Never commit
  `build/out/` or `build/fleet.config.json`.

## When you finish

Tell the operator, in five lines or fewer: what exists now (the lists, the flows, the app and the links), every
fix you made and where it is recorded, and the next thing to do, which is `TESTING.md` §3, the first prompt round
trip.
