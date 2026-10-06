# Koa: instructions for GitHub Copilot

Koa is the phone side of the fleet. It holds the FleetAgent canvas app (`powerapp/src/*.pa.yaml`), its two Power
Automate flows (`flows/*.definition.json`), the SharePoint list workbook (`data/`) and the pinned contract with the
laptop (`contract/`). `AGENTS.md` holds the repository rules, and they apply to you.

- **To build the Data Czars site's lists,** use the `build-czars-site` skill (`.github/skills/build-czars-site/SKILL.md`);
  the site's pages, navigation, skill and agent are the operator's, with Copilot in SharePoint (`site/README.md`).
- **To build or deploy the app, the lists or the flows,** use the `build-fleetagent` skill
  (`.github/skills/build-fleetagent/SKILL.md`). It walks `build/steps/01`-`07` and keeps its progress in
  `build/out/state.json`.
- **The app is designed; you deploy it.** Do not regenerate screens with the canvas-apps plugin's `/canvas-app`
  create workflow. Copy the repository's sources in with `python build/prepare.py canvas-in`, then compile and
  fix what the validator rejects (`build/steps/06-app.md`).
- **The contract is pinned.** Never edit `contract/`. `tests/test_contract.py` fails on any changed byte.
- **The app decides nothing.** It shows the laptop's words verbatim, so do not add logic that interprets a
  state.
- **Before you commit,** run `python -m pip install -r requirements-dev.txt` once, then `python -m pytest -q`.
