---
name: build-czars-site
description: Builds the Data Czars SharePoint site from this repository and the facts scanned from data-czars, usage_tool and the team's Confluence pages - the context, the lists and library with their formatting and rows, the intake and report flows, and the filled-in page and agent prompts - without any MCP server or agent plugin, by writing the packages the operator imports and checking the run report they save. Use when asked to build, provision, set up, rebuild or update the Data Czars site, its lists, its flows, or the site in site/.
---

# Build the Data Czars site

You are building a site that is already designed. `site/lists.json`, `site/formatting/`, `site/pages/` and
`site/agents/` are reviewed sources: put them on the operator's site exactly as they are. Do not add, rename or drop
a list, column, view, section or web part. The facts that fill them come from `site/local/context.json`, which the
scans write (`site/README.md`, step 0). You do steps 0 (checking), 2 and 6 of `site/README.md`, and render step 5's
prompts; the pages, the navigation, the site skill and the agents are the operator's, with Copilot.

**You have no MCP tools, and you never will here.** The organisation blocks MCP servers, so there is no FlowAgent
and no Microsoft Learn server. Never call one, never ask the operator to install one or a plugin that brings one, and
never wait for one. You run `python site/provision.py`, which writes the packages the operator imports and checks
what they save from a run; everything in Power Automate and SharePoint happens in the operator's browser.

## Before anything

1. Read `site/README.md`, `site/intake/README.md`, then `.github/copilot-instructions.md`.
2. Read `site/out/state.json` if it exists, and resume from what it records.

## Steps

1. **The context.** If `site/local/context/` holds no scan, tell the operator to run the three scans and the
   Microsoft Copilot prompt (`site/README.md`, step 0) and stop. Otherwise run `python site/provision.py context`.
   For every gap it names, ask the operator in one message, write their answers to
   `site/local/context/00-operator.json`, and run it again until it names none.
2. **Check.** `python site/provision.py check`. A refusal is a defect: report it and stop.
3. **The lists.** `python site/provision.py flow` writes `site/out/CzarsProvisionSite.zip`. Send the operator, with
   the path filled in:

   > In https://make.powerautomate.com: **My flows** > **Import** > **Import Package (Legacy)** > **Upload**
   > `<path>\site\out\CzarsProvisionSite.zip`. The flow's **Import setup**: **Create as new** (or **Update** if it is
   > there) > **Save**; **SharePoint**: your connection > **Save**; **Import** > **Open flow** > **Run** > **Run
   > flow**. When the run ends, open its last action, **Report**, **Show raw outputs**, copy all of it and save it as
   > `<path>\site\out\provision-report.json`. Reply when it is saved, or paste the first red step's error.

   Then `python site/provision.py check-run site/out/provision-report.json`. Every line it prints is the step's
   result, quoted exactly; `lists: ready` means every script applied and every starter row is there. After a fix the
   flow is safe to run again. When it passes, the operator may delete the flow.
4. **The intake and report flows.** Ask the operator for the OneDrive id of `DataCzars/results`, as
   `site/intake/README.md` *Set it up* 2 says (create `DataCzars/intake` and `DataCzars/results` first if they are
   missing), then `python site/provision.py flows --results-folder-id <id>`. Have the operator import
   `CzarsIntakeOut.zip`, `CzarsIntakeBack.zip` and `CzarsTagReports.zip` the same way, picking their SharePoint and
   OneDrive for Business connections, and turn each one on. These stay on.
5. **The prompts.** `python site/provision.py pages` writes the filled-in page and agent prompts to `site/out/`.
6. **A first ticket**, with the operator: they submit a test issue on the site; within a minute
   `intake-<id>.json` appears; `python site/intake/intake.py file <id> --dry-run` shows the ticket. Filing it for
   real is the operator's choice: it asks for their approval.

## State file

`site/out/state.json`: `{"status": "done" | "waiting" | "blocked", "at": "<UTC>", "notes": "...", "flows": {"<name>":
"imported"}, "outcomes": {"<list>": "<summary>"}}`. Never a token, password or secret, and nothing from the context.

## Rules

- **Every write is idempotent.** Scripts update what they made; rows are added only when their Title is missing; a
  package imported again with **Update** replaces its flow. Never delete a list, column, view or row on the site.
- **The context stays local.** Never copy anything from `site/local/` into a tracked file, a commit or a pull request.
- **Two refusals in a row stop you.** The same import or run failing twice the same way: mark `blocked` with the
  step, the file, the error (no context values) and what you tried, and tell the operator. If the import page
  refuses the package itself, that is row S15: take route B or C of `site/README.md` step 2 instead.
- **Fix only what Power Automate or SharePoint names.** If a run rejects a parameter of a SharePoint or OneDrive
  action, ask the operator to open that action in the flow and read you its parameter names; correct
  `site/provision.py`, run `python -m pytest -q`, regenerate, and note the fix in the pull request that carries it.

## When you finish

Tell the operator, in five lines or fewer: the lists that exist now, the flows that are on, any outcome that was not a
success, the rows of `site/README.md` *What only the tenant can prove* you saw (S1 to S4, S11, S15), and the next step,
which is `site/README.md` step 3.
