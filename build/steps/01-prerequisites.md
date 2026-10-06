# Step 01: prerequisites and the config

**Who:** you. The operator signs in when a window opens and answers two questions.
**Produces:** every tool checked, and `build/fleet.config.json` filled in with `environment`, `siteUrl`, `library`
and `operators`.

## 1. The tools

Run each check and compare it with the expected result. On a miss, tell the operator the fix in the third column
and wait.

| Run | Expect | Fix |
| --- | --- | --- |
| `python --version` | 3.10 or later | install Python 3.12+ |
| `dotnet --list-sdks` | a line starting `10.` or higher | install the .NET 10 SDK, then restart the agent |
| `node --version` | v18 or later | install Node.js LTS, then restart the agent |
| `az account show --query user.name -o tsv` | the operator's UPN | `az login --allow-no-subscriptions` (a browser opens; the operator signs in) |
| FlowAgent `whoami` | the same UPN | FlowAgent `doctor`; it names what is missing. Sign-ins go through `az login` |
| canvas MCP tool `connect` is listed among your tools | present | install the canvas-apps plugin (`build/README.md` §2) and restart |

Then `python -m pip install -r requirements-dev.txt` and `python -m pytest -q`. They must pass before you
change anything; if they do not, stop. The repository is broken, not the tenant.

## 2. The environment

Call FlowAgent `list_environments`.

- If there is exactly one, or exactly one is marked default and the operator has no preference, use it.
- Otherwise ask the operator which one. The app, both flows and the connections must all live in that same
  environment.

Call `set_current_env` with it, and record its id as `environment`.

## 3. The operators and the site

Several operators share one site: each has their own fleet and laptop, and they all see one app. Ask the operator
who is running this build:

> 1. Which SharePoint site holds FleetAgent? Paste its address, for example
>    `https://contoso.sharepoint.com/sites/FleetAgent`. It must be a team or communication site you **own**:
>    the build locks the lists and the bridge library to the site's Owners, and cloud connections cannot reach a
>    personal site's "My lists".
> 2. Who are the operators? The UPN (sign-in address) of each person whose fleet will use it, yourself included.
>    Every one of them must be an Owner of that site.

Record the site as `siteUrl` (no trailing slash, no page name) and the UPNs, lowercase, as `operators`. Keep
`library` as `FleetAgent` unless the site already has a library of that name used for something else.

Nobody's laptop changes in this step. Each operator connects their own laptop after the build, following
[build/each-operator.md](../each-operator.md).

## 4. Write and check the config

If `build/fleet.config.json` does not exist, copy `build/fleet.config.example.json` to it. Fill in `environment`,
`siteUrl`, `library` and `operators`, and leave `studioUrl` and `appId` empty for now. Then run:

```
python build/prepare.py check
```

**Check:** the output says `lists: ready`, and `flows:` is missing only `appId`.

Record step 01 as `done` in `build/out/state.json`, including the environment's display name, and go to step 02.
