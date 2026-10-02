# Step 01: prerequisites and the config

**Who:** you. The operator signs in when a window opens and answers two questions.
**Produces:** every tool checked, and `build/fleet.config.json` filled in with `environment`, `siteUrl`, `operator`,
`outboxFolderPath` and `inboxFolderPath`.

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

## 3. The laptop's bridge

The flows read and write the folder the laptop's bridge syncs. Run `ad-fleet mobile status`.

- **The command exists and `folder` is set:** the OneDrive path is the part of `folder` after the OneDrive root.
  `C:\Users\me\OneDrive - Contoso\FleetAgent` becomes `/FleetAgent`. Set `outboxFolderPath` to
  `/FleetAgent/outbox` and `inboxFolderPath` to `/FleetAgent/inbox`, with your actual folder name. Take
  `operator` from the status output.
- **`ad-fleet` exists but the bridge is off or has no folder:** tell the operator to run
  `ad-setup --patch fleet.mobile` with these answers:
  - enabled: yes;
  - folder: `%OneDriveCommercial%/FleetAgent`;
  - operator: their UPN;
  - expire_s: 900;
  - notify: yes.

  Then they run `ad-fleet mobile init`. Run the status again afterwards.
- **`ad-fleet` is not installed on this machine:** the bridge runs on another laptop. Ask the operator for the
  bridge folder's name under their OneDrive and for their UPN.

Check that the folder exists in OneDrive and is synced. A `pairing.json` file inside it means `init` ran.

## 4. The SharePoint site

Ask the operator:

> Which SharePoint site should hold the five FleetAgent lists? Paste its address, for example
> `https://contoso.sharepoint.com/sites/FleetAgent`. If you have none, create one: SharePoint home > **Create
> site** > **Team site**, name it `FleetAgent`, private.

Record the address as `siteUrl`, with no trailing slash and no page name.

## 5. Write and check the config

If `build/fleet.config.json` does not exist, copy `build/fleet.config.example.json` to it. Fill in the five values
above and leave `studioUrl`, `appId` and `outboxFolderId` empty for now. Then run:

```
python build/prepare.py check
```

**Check:** the output says `lists: ready`. It says `flows:` is missing only `outboxFolderId` and `appId`.

Record step 01 as `done` in `build/out/state.json`, including the environment's display name, and go to step 02.
