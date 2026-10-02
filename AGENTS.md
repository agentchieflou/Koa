# Koa: rules for coding agents

Koa is the phone side of the fleet: the FleetAgent canvas app (`powerapp/`), the two flows (`flows/`), the list
workbook (`data/`) and the pinned mobile contract (`contract/`). The laptop side, and the rules for agents working
on it, live in [agentchieflou/this-next-please](https://github.com/agentchieflou/this-next-please) (`AGENTS.md`,
`docs/developing-with-agents.md`, `docs/plan-mobile.md`, `docs/fleet-mobile.md`). Read `README.md` here first.

1. **One PR at a time; the operator merges.** No trains here (this-next-please#600, D11). Conventional Commits.
2. **The contract is pinned, never edited.** `contract/` changes only by adopting a published
   `mobile-contract-v*` tag: replace the schema and examples from the tag and rewrite `contract/PIN` in the same
   PR. `tests/test_contract.py` fails on any byte that does not match the pin.
3. **Never import `agentdata`.** The laptop's vocabulary (states, roles, severities, columns) comes from the
   contract. `tests/test_contract.py` enforces it.
4. **The app decides nothing.** It shows `State`, `Says` and every error in the laptop's or the flow's own words and
   colours by `Role`; `tests/test_mobile_powerapp.py` holds it to that.
5. **Bytes are exact.** `.gitattributes` is `* -text`; every source is UTF-8, LF, no trailing whitespace.
6. **Never skip, xfail or loosen a test.** Run `python -m pip install -r requirements-dev.txt` and
   `python -m pytest -q` before every push; CI runs the same on Ubuntu and Windows (`core.autocrlf=true`).
7. **What only Studio, the tenant or a phone can prove reads *not yet measured*** until someone ran it, and the
   run is recorded in this-next-please's `docs/windows-verification.md` §Mobile ([TESTING.md](TESTING.md)).
