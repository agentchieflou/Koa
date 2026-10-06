---
name: build-fleetagent
description: Builds the FleetAgent mobile app end to end on Microsoft 365 from this repository - the five SharePoint lists, the FleetDecide and FleetOutboxToLists flows, and the canvas app from powerapp/src - without any MCP server or agent plugin, by writing the files the operator imports and pastes in the browser and checking what they paste back. Use when asked to build, set up, deploy, install, rebuild or continue building FleetAgent, the Power App, the mobile app, the lists or the flows.
---

# Build FleetAgent

You are deploying an app that is already designed. `powerapp/src`, `flows/` and `contract/` are finished,
reviewed sources: your job is to get them into the operator's tenant exactly as they are, and to fix only what
Power Automate or Studio rejects. Do not redesign a screen, rename a control, add a feature, or "improve" a formula.

**You have no MCP tools, and you never will here.** The organisation blocks MCP servers, so there is no FlowAgent,
no Canvas Authoring server and no Microsoft Learn server. Never call one, never ask the operator to install one or a
plugin that brings one, and never wait for one. You work with files and the terminal: `python build/prepare.py`
writes what the operator imports or pastes, and checks what they save from a run. Everything in Power Automate,
Power Apps and SharePoint happens in the operator's browser, by the operator, in the words the step gives you.

## Before anything

1. Read `build/README.md` (what the operator does and what you do), then `.github/copilot-instructions.md`.
2. Read `build/out/state.json` if it exists. It records the steps already done and the values found. Resume at
   the first step not marked `done`. If the file does not exist, start at step 01.

## The steps

Do them in order. Do each one completely: run the step's **Check** and record the result in
`build/out/state.json` before you open the next file.

| Step | File | Who | Produces |
| --- | --- | --- | --- |
| 01 | `build/steps/01-prerequisites.md` | you; the operator answers | tools checked, `build/fleet.config.json` filled (environment, siteUrl, library, operators) |
| 02 | `build/steps/02-lists.md` | you write the flow; the operator imports and runs it | the five lists with every column and index, the bridge library with one folder per operator, all six locked to the site's Owners |
| 03 | `build/steps/03-decide-flow.md` | you write the package; the operator imports it | `FleetDecide`, on |
| 04 | `build/steps/04-app-shell.md` | the operator, guided by you | a blank Tablet app with its settings; `studioUrl`, `appId` |
| 05 | `build/steps/05-outbox-flow.md` | you write the packages; the operator imports them and changes owners | one `FleetOutboxToLists (<UPN>)` per operator, on, each reading only that operator's folder and owned by them |
| 06 | `build/steps/06-app.md` | the operator adds data and pastes; you fix what Studio reports | every screen, component and the App object in Studio, with no errors in the App checker |
| 07 | `build/steps/07-finish.md` | the operator publishes, shares and saves the app; you mirror it and verify | a published app shared with every operator, the repository mirrored and tested, the first round trip ready |

## State file

Write `build/out/state.json` as `{"steps": {"01": {"status": "done", "at": "<UTC>", "notes": "..."}, ...},
"flows": {"FleetDecide": "imported", ...}}`. `status` is one of `done`, `waiting` (on the operator; say for what)
or `blocked` (say why). Never put a token, password or secret in it.

## Rules for the whole build

- **The browser is the operator's.** When a step says *Operator*, send them the step's message, with the values
  filled in, and wait for their reply. Never claim something happened in the tenant until the operator has said so
  or pasted what shows it.
- **Read back, don't assume.** Where a step asks the operator to save a run's output or paste Studio's errors, check
  it with the command the step names (`check-lists`) or against the step's table before you mark the step `done`.
- **Every import is repeatable.** A package imported again with **Update** replaces the flow of that name; a list
  flow run again changes nothing that is already right. Prefer **Update** when a flow of that name exists.
- **Two refusals in a row stop you.** If the operator reports the same error twice for the same import or paste, mark
  the step `blocked` with the step, the file, the error text and what you tried, and tell the operator. Do not loop.
  Every step names the hand-built fallback for when an import itself is refused.
- **Fix what Power Automate and Studio say, and nothing else.** A rejected import or a Studio error is fixed in the
  smallest edit that clears it, in the repository's copy (`flows/` or `powerapp/src`). Each fix is written into
  `powerapp/NOTES.md` (app) or `flows/README.md` "Verify on import" (flows), naming the error and the change. Run
  `python -m pytest -q` after every change to a tracked file.
- **Nothing tenant-specific in tracked files.** Site URLs, ids, UPNs and folder ids live in
  `build/fleet.config.json` and `build/out/`, which git ignores. The tests refuse them anywhere else.
- **Commit only the repository's own changes.** That means `powerapp/`, `flows/` and doc rows. Never commit
  `build/out/` or `build/fleet.config.json`.

## When you finish

Tell the operator, in five lines or fewer: what exists now (the lists, the flows, the app and the links), every
fix you made and where it is recorded, and the next thing to do, which is `TESTING.md` §3, the first prompt round
trip.
