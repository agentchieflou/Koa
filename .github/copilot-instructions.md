# Koa: instructions for GitHub Copilot

Koa is the phone side of the fleet. It holds the FleetAgent canvas app (`powerapp/src/*.pa.yaml`), its two Power
Automate flows (`flows/*.definition.json`), the SharePoint list workbook (`data/`) and the pinned contract with the
laptop (`contract/`). `AGENTS.md` holds the repository rules, and they apply to you.

**No MCP servers.** The organisation blocks them, so this repository is built without any: no FlowAgent, no
Canvas Authoring server, no Microsoft Learn server, no agent plugin that brings one. Never call an MCP tool, never
ask the operator to install or enable a server, a plugin or an extension that adds one, and never wait for one to
appear. Everything you do here is reading and editing files and running `python` (and `git`) in the terminal. What
happens in Power Automate, Power Apps or SharePoint is the operator's, in their browser: you write the file they
import or paste, tell them the clicks exactly as the step words them, and read back what they paste into the chat.
A Microsoft Learn link in these files is for the operator to open; when you need a fact from Microsoft's documentation
that the repository does not hold, say which page and ask the operator, and never guess.

- **To build the Data Czars site's lists,** use the `build-czars-site` skill (`.github/skills/build-czars-site/SKILL.md`);
  the site's pages, navigation, skill and agents are the operator's, with Copilot in SharePoint (`site/README.md`).
  To gather the facts its pages need, run the `czars-scan-*` prompts (`.github/prompts/`); they write only to
  `site/local/`, which is never committed.
- **To build or deploy the app, the lists or the flows,** use the `build-fleetagent` skill
  (`.github/skills/build-fleetagent/SKILL.md`). It walks `build/steps/01`-`07` and keeps its progress in
  `build/out/state.json`.
- **The app is designed; you deploy it.** Never regenerate or redesign a screen. The operator pastes the repository's
  sources into Studio in the order `python build/prepare.py paste` gives, and you fix only what Studio's App checker
  reports, in `powerapp/src` (`build/steps/06-app.md`).
- **The contract is pinned.** Never edit `contract/`. `tests/test_contract.py` fails on any changed byte.
- **The app decides nothing.** It shows the laptop's words verbatim, so do not add logic that interprets a
  state.
- **Before you commit,** run `python -m pip install -r requirements-dev.txt` once, then `python -m pytest -q`.
