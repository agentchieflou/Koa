---
description: Find which repositories the operator's fleet runs and write the fleet page's facts to site/local/context/fleet.json. Read-only.
---
# Scan the fleet for the site

The Data Czars site has one page about the fleet: the agents, one per repository, that work the team's tickets.
Its words come from this-next-please (public, already in `site/pages/fleet.md`). What only this laptop knows is
which repositories the fleet runs; that is what you collect.

## Rules

1. **Read only.** The only commands you may run are `ad-fleet status` and `ad-fleet repo list` if they exist; they
   change nothing. Never start, stop or answer an agent.
2. Repository names only: never a ticket's text, an agent's conversation or a file from another repository.

## Collect

- **`fleet.repos`**: the names of the registered repositories, as `ad-fleet` prints them. If `ad-fleet` is not
  installed, list the folders beside Koa that hold an `AGENTS.md` declaring a `jira_project`, and add a gap saying
  the list was inferred.
- **`fleet.summary`**: one sentence, starting from "Several agents, one per repository, watched and answered from one
  window", that names how many repositories the team's fleet runs and that data-czars and usage_tool are among them
  if they are.
- **`fleet.source`**: the command or the method you used.

## Write

Write `site/local/context/fleet.json` with only `fleet` and `gaps`, then run `python site/provision.py context`.

## Finish

Two lines: the repositories, and the next step, which is the Microsoft 365 Copilot prompt in
`site/prompts/m365-org-facts.md`.
