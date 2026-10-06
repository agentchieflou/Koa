# Step 01: prerequisites and the config

**Who:** you. The operator answers three questions.
**Produces:** the laptop checked, and `build/fleet.config.json` filled in with `siteUrl`, `library` and `operators`
(step 04 adds `environment`, `studioUrl` and `appId` from the Studio URL).

There is nothing to install and nothing to sign in to here: the build uses no MCP server and no agent plugin. If
the operator mentions FlowAgent, the canvas-apps or power-automate plugins, or `az login`, tell them none of it is
needed.

## 1. The laptop

Run each check and compare it with the expected result. On a miss, tell the operator the fix in the third column
and wait.

| Run | Expect | Fix |
| --- | --- | --- |
| `python --version` | 3.10 or later | install Python 3.12+ |
| `git --version` | any | install Git for Windows, or unzip GitHub's *Download ZIP* instead of cloning |

Then `python -m pip install -r requirements-dev.txt` and `python -m pytest -q`. They must pass before you
change anything; if they do not, stop. The repository is broken, not the tenant.

## 2. The operators, the site and the environment

Several operators share one site: each has their own fleet and laptop, and they all see one app. Ask the operator
who is running this build, in one message:

> 1. Which SharePoint site holds FleetAgent? Paste its address, for example
>    `https://contoso.sharepoint.com/sites/FleetAgent`. It must be a team or communication site you **own**:
>    the build locks the lists and the bridge library to the site's Owners, and cloud connections cannot reach a
>    personal site's "My lists".
> 2. Who are the operators? The UPN (sign-in address) of each person whose fleet will use it, yourself included.
>    Every one of them must be an Owner of that site.
> 3. Which Power Platform environment? Open https://make.powerautomate.com and read the name in the environment
>    picker at the top right. The flows and the app must all be made in that one environment; if you have more
>    than one, pick the one your team's other flows live in.

Record the site as `siteUrl` (no trailing slash, no page name) and the UPNs, lowercase, as `operators`. Keep
`library` as `FleetAgent` unless the site already has a library of that name used for something else. Record the
environment's name in the state file's notes; its id comes from the Studio URL in step 04.

Nobody's laptop changes in this step. Each operator connects their own laptop after the build, following
[build/each-operator.md](../each-operator.md).

## 3. Write and check the config

If `build/fleet.config.json` does not exist, copy `build/fleet.config.example.json` to it. Fill in `siteUrl`,
`library` and `operators`, and leave `environment`, `studioUrl` and `appId` empty for now. Then run:

```
python build/prepare.py check
```

**Check:** the output says `lists: ready`, and `flows:` is missing only `appId`.

Record step 01 as `done` in `build/out/state.json`, including the environment's name, and go to step 02.
