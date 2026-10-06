---
name: build-czars-site
description: Builds the Data Czars SharePoint site from this repository and the facts scanned from data-czars, usage_tool and the team's Confluence pages - the context, the lists and library with their formatting and rows, the intake and report flows, and the filled-in page and agent prompts - through the power-automate plugin. Use when asked to build, provision, set up, rebuild or update the Data Czars site, its lists, its flows, or the site in site/.
---

# Build the Data Czars site

You are building a site that is already designed. `site/lists.json`, `site/formatting/`, `site/pages/` and
`site/agents/` are reviewed sources: put them on the operator's site exactly as they are. Do not add, rename or drop
a list, column, view, section or web part. The facts that fill them come from `site/local/context.json`, which the
scans write (`site/README.md`, step 0). You do steps 0 (checking), 2 and 6 of `site/README.md`, and render step 5's
prompts; the pages, the navigation, the site skill and the agents are the operator's, with Copilot.

## Before anything

1. Read `site/README.md`, `site/intake/README.md`, then `.github/copilot-instructions.md`.
2. Read `site/out/state.json` if it exists, and resume from what it records.
3. Confirm the FlowAgent tools are present (`list_environments`, `create_flow`, `run_flow`,
   `pick_or_create_connection` and so on; prefixed `flowagent-` in Copilot CLI). If they are missing, tell the
   operator to install the `power-automate` plugin as `build/README.md` §2 says, and stop.

## Steps

1. **The context.** If `site/local/context/` holds no scan, tell the operator to run the three scans and the
   Microsoft Copilot prompt (`site/README.md`, step 0) and stop. Otherwise run `python site/provision.py context`.
   For every gap it names, ask the operator in one message, write their answers to
   `site/local/context/00-operator.json`, and run it again until it names none.
2. **Check.** `python site/provision.py check`. A refusal is a defect: report it and stop.
3. **The connections.** `pick_or_create_connection` for `shared_sharepointonline` and for
   `shared_onedriveforbusiness`; the operator approves each consent window the first time.
4. **The lists.** `python site/provision.py flow` writes `site/out/CzarsProvisionSite.json`. `preflight_flow` (or
   `validate_flow`) it; `list_flows`, then `update_flow` if it exists or `create_flow`; `publish_flow`; `run_flow`
   with `wait: true`. Read every `Apply_script` output in `For_each_script` (`get_run_action_repetitions`): any outcome
   other than success is the step's result, quoted exactly. Run it a second time: every `Add_row` must be skipped.
   Then `delete_flow`.
5. **The intake and report flows.** Find the OneDrive id of `DataCzars/results` (create `DataCzars/intake` and
   `DataCzars/results` first if they are missing), then `python site/provision.py flows --results-folder-id <id>`.
   For each of `CzarsIntakeOut`, `CzarsIntakeBack` and `CzarsTagReports`: `preflight_flow`, create or update,
   `publish_flow`. These stay on.
6. **The prompts.** `python site/provision.py pages` writes the filled-in page and agent prompts to `site/out/`.
7. **A first ticket**, with the operator: they submit a test issue on the site; within a minute
   `intake-<id>.json` appears; `python site/intake/intake.py file <id> --dry-run` shows the ticket. Filing it for
   real is the operator's choice: it asks for their approval.

## State file

`site/out/state.json`: `{"status": "done" | "waiting" | "blocked", "at": "<UTC>", "notes": "...", "flows": {"<name>":
"<id>"}, "outcomes": {"<list>": "<summary>"}}`. Never a token, password or secret, and nothing from the context.

## Rules

- **Every write is idempotent.** Scripts update what they made; rows are added only when their Title is missing.
  Never delete a list, column, view or row on the site.
- **The context stays local.** Never copy anything from `site/local/` into a tracked file, a commit or a pull request.
- **Two refusals in a row stop you.** The same call failing twice the same way: mark `blocked` with the tool, the
  arguments (no secrets, no context values), the error and what you tried, and tell the operator.
- **Fix only what a validator names.** If `preflight_flow` rejects a parameter of a SharePoint or OneDrive action,
  read `get_operation_details` for that connector and operation, correct `site/provision.py`, run
  `python -m pytest -q`, regenerate, and note the fix in the pull request that carries it.

## When you finish

Tell the operator, in five lines or fewer: the lists that exist now, the flows that are on, any outcome that was not a
success, the rows of `site/README.md` *What only the tenant can prove* you saw (S1 to S4, S11), and the next step,
which is `site/README.md` step 3.
