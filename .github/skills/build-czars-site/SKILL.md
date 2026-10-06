---
name: build-czars-site
description: Builds the Data Czars SharePoint site's lists from this repository - the twelve lists and the Guides library with their columns, views, formatting and starter rows - through a one-shot provisioning flow and the power-automate plugin. Use when asked to build, provision, set up, rebuild or update the Data Czars site, its lists, or the site in site/.
---

# Build the Data Czars lists

You are provisioning lists that are already designed. `site/lists.json` and `site/formatting/` are reviewed sources:
put them on the operator's site exactly as they are. Do not add, rename or drop a list, column or view. The pages,
the navigation, the site skill and the agent are built afterwards by the operator with Copilot in SharePoint
(`site/README.md`, steps 3 to 6); you only do step 2.

## Before anything

1. Read `site/README.md` (steps 1, 2 and *What only the tenant can prove*), then `.github/copilot-instructions.md`.
2. Read `site/out/state.json` if it exists, and resume from what it records.
3. Confirm the FlowAgent tools are present (`list_environments`, `create_flow`, `run_flow`,
   `pick_or_create_connection` and so on; prefixed `flowagent-` in Copilot CLI). If they are missing, tell the
   operator to install the `power-automate` plugin as `build/README.md` §2 says, and stop.

## Steps

1. **Check the spec.** `python site/provision.py check`. A refusal is a defect in the repository: report it and stop.
2. **The site.** Ask the operator for the site's address (`https://<tenant>.sharepoint.com/sites/OSP-Data-Czars`)
   and their Power Platform environment if they have more than one. Record both in `site/out/state.json`.
3. **The flow.** `python site/provision.py flow --site <address>` writes `site/out/CzarsProvisionSite.json`
   (`{name, definition, connectors, connectionRefsTemplate}`).
4. **The connection.** `pick_or_create_connection` for `shared_sharepointonline`; the operator approves the consent
   window if one opens. Put the connection name into the template's `connectionName`.
5. **Create, turn on, run.** `preflight_flow` (or `validate_flow`) with the definition and the connection references.
   `list_flows`: if `CzarsProvisionSite` exists, `update_flow` on it; otherwise `create_flow`. Then `publish_flow`,
   then `run_flow` with `wait: true`.
6. **Read every outcome.** `get_run_actions`, then `get_run_action_repetitions` for `For_each_script`. Each
   `Apply_script` output lists one result per script action with an outcome code: anything other than success is
   the step's result, quoted exactly. A 403 means the operator is not an owner of the site. A 400 or 404 on
   `ExecuteTemplateScript` itself means the tenant refuses the endpoint: mark the step `blocked` and give the
   operator `site/README.md` step 2 B and the admin route; do not try another way.
7. **Run it again.** `run_flow` with `wait: true` a second time. Every `Add_row` must be skipped (the starter rows
   exist) and every script must succeed again. That proves the provisioning is repeatable.
8. **Clean up.** `delete_flow` on `CzarsProvisionSite`; `provision.py flow` can regenerate it at any time.

## State file

`site/out/state.json`: `{"site": "<address>", "environment": "<id>", "status": "done" | "waiting" | "blocked",
"at": "<UTC>", "notes": "...", "outcomes": {"<list>": "<summary>"}}`. Never a token, password or secret.

## Rules

- **Every write is idempotent.** Scripts update what they made; rows are added only when their Title is missing.
  Never delete a list, column, view or row on the site.
- **Two refusals in a row stop you.** The same call failing twice the same way: mark `blocked` with the tool, the
  arguments (no secrets), the error and what you tried, and tell the operator.
- **Fix only what a validator names.** If `preflight_flow` rejects a parameter name of the SharePoint action, read
  `get_operation_details` for `shared_sharepointonline` / `HttpRequest`, correct `_sp()` in `site/provision.py`, run
  `python -m pytest -q`, and regenerate. Note the fix in the pull request that carries it.
- **Nothing tenant-specific in tracked files.** The site address lives in `site/out/`, which git ignores.

## When you finish

Tell the operator, in five lines or fewer: the lists that exist now, any outcome that was not a success, the rows
S1 to S4 of `site/README.md` *What only the tenant can prove* with what you saw, and the next step, which is
`site/README.md` step 3.
