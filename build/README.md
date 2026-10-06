# Building FleetAgent with a Copilot agent

This folder lets a GitHub Copilot agent build everything on the Microsoft 365 side, end to end:

- the five SharePoint lists, and the library that holds each operator's bridge folder, all readable by the site's
  Owners only;
- the flows: `FleetDecide`, which every operator's phone calls, and one copy of `FleetOutboxToLists` per operator,
  which reads only that operator's folder;
- the FleetAgent canvas app, built from the sources in `powerapp/src`.

Several operators share it: each runs their own fleet on their own laptop, and everyone sees one app. The build is
done once, by one of them. Then each operator connects their own laptop and phone with
[each-operator.md](each-operator.md), which takes about five minutes.

The agent does the building. You put the files in place, sign in when a window asks, and do the few clicks that
Microsoft does not allow any tool to do. Those clicks are listed below, and the agent stops and tells you when
each one is due.

The agent works through Microsoft's own plugins for coding agents, from
[microsoft/power-platform-skills](https://github.com/microsoft/power-platform-skills):

- **canvas-apps**: the Canvas Authoring MCP server. It validates `.pa.yaml` and writes it into a live Power
  Apps Studio session ([Learn](https://learn.microsoft.com/power-apps/maker/canvas-apps/create-canvas-external-tools)).
- **power-automate**: the FlowAgent MCP server. It creates, turns on, runs and debugs cloud flows, and finds or
  creates connections. It signs in through `az login`.

## 1. Put the files in place

| What | Where | Why |
| --- | --- | --- |
| This repository, the whole of it | any folder on the Windows laptop, for example `C:\src\Koa` (`git clone https://github.com/agentchieflou/Koa`, or unzip GitHub's *Download ZIP*) | the agent reads `powerapp/`, `flows/`, `contract/` and `build/` from here |
| `build/fleet.config.example.json` | copy it to `build/fleet.config.json` in the same folder; leave the values for the agent to fill in | git ignores the copy; it holds this tenant's addresses, never a secret |
| the bridge folders | nothing to copy: step 02 creates one per operator in the site's `FleetAgent` library, and each operator syncs their own as a OneDrive shortcut ([each-operator.md](each-operator.md)) | the flows watch every `outbox\` and write the sender's own `inbox\` |

Nothing else needs moving. The agent finds its instructions without being told where to look:

- `.github/copilot-instructions.md`: the rules every Copilot session in this folder follows.
- `.github/skills/build-fleetagent/SKILL.md`: the build, as a skill Copilot loads by name.
- `build/steps/01-...07-*.md`: the seven steps the skill walks through.
- `build/prepare.py`: the one script the steps run. It needs Python 3.10 or later and the standard library only.

## 2. Install once

1. **A Copilot agent with plugin support.** Choose one:
   - **GitHub Copilot CLI**: `npm install -g @github/copilot`, then run `copilot` in the repository folder.
   - **VS Code** with GitHub Copilot, using Chat in **Agent** mode.
2. **The .NET 10 SDK** ([download](https://dotnet.microsoft.com/download/dotnet/10.0)). The canvas MCP server runs
   on it. Check it with `dotnet --list-sdks`: a line must start with `10.`
3. **Node.js 18 or later.** The FlowAgent MCP server runs on it.
4. **Azure CLI**: `az login --allow-no-subscriptions`. The laptop usually has this already, for `ad-pbi`.
5. **The two plugins.**
   - **In Copilot CLI:**

     ```
     /plugin marketplace add microsoft/power-platform-skills
     /plugin install canvas-apps@power-platform-skills
     /plugin install power-automate@power-platform-skills
     ```

   - **In VS Code:** open Extensions, search `@agentPlugins canvas apps` and `@agentPlugins power automate`, and
     install both (published by Microsoft). If nothing shows up, add `"chat.plugins.enabled": true` to your user
     settings.
6. Restart the agent, so it starts the two MCP servers.

If your organisation blocks agent plugins, local MCP servers or `api.nuget.org`, the build cannot run. Step 01
names the blocked piece, and the manual build sheets (`README.md`, `flows/README.md`, `data/README.md`) still work.

## 3. Start the build

In the repository folder, tell the agent:

> Build FleetAgent. Use the build-fleetagent skill.

The agent asks for three things: your SharePoint site's address, your Power Platform environment if you have more
than one, and the Studio URL once you have made the blank app. It records what it has done in
`build/out/state.json`, so if a session ends you can say the same sentence again and it continues where it
stopped.

## 4. What only you can do

The agent stops, tells you exactly what to click, and waits for you each time:

| When | You do | Time |
| --- | --- | --- |
| step 01 | sign in when `az login` and each MCP server open a browser window | 1 min |
| step 01 | give the SharePoint site's address and every operator's UPN. The site must be a team or communication site where all of you are **Owners**; cloud connections cannot reach a personal site's "My lists" | 2 min |
| steps 02, 03, 05 | approve each connection consent window the first time a connector is used: SharePoint, Office 365 Users, Power Apps Notification | 1 min |
| step 04 | create the blank app in Studio and change four settings (step 04 lists each click), then paste the Studio URL into the chat | 3 min |
| step 05 | change each operator's copy of `FleetOutboxToLists` to be owned by that operator (step 05 lists each click), so each copy runs on its owner's daily request limit | 3 min |
| step 06 | in Studio, add the five lists and the `FleetDecide` flow through **Data** > **Add data**. The canvas plugin itself says no tool can do this | 2 min |
| step 07 | paste the theme (optional), **Publish**, **Share** the app with the other operators, and add them to `FleetDecide`'s run-only users | 5 min |
| after the build, each operator | add a shortcut to their own bridge folder, point their laptop's bridge at it, and open the app once on the phone ([each-operator.md](each-operator.md)) | 5 min |

Everything else is the agent's: the lists, their columns and indexes, the bridge library and folders, the
Owners-only lock and its proof, the flows and their connections, every
screen, component and formula of the app, the compile-and-fix loop, and the repository's tests.

## Owners only

Step 02 cuts the five lists and the library off from the site's permissions and grants the site's **Owners** group
Full Control, and nobody else. It then reads the permissions back and fails the step if anyone else is left. Every
flow and the app act as one of the operators, who are all Owners, so nothing breaks. Anyone else, including a site
Member or someone the app is shared with by mistake, sees no lists and no files. One consequence: whoever becomes
an Owner of the site later can read every operator's fleet.

## The Created column

Every SharePoint list already has a column called `Created`: the date and time the row was made. The contract's
`FleetApprovals.Created` (the request's own creation time, as text) cannot be a second column with that name. So:

- the lists are made without it;
- `FleetOutboxToLists` no longer writes it;
- the app reads `Created` in a way that works for SharePoint's date and for the Excel fallback's text.

The row is created when the flow sees the request, which is within one OneDrive sync and one trigger poll of the
request's own `created`.

## When the agent stops

Each step ends in **Done**, **Waiting for you** (one of the clicks above), or **Blocked**. Blocked means a tool
refused twice in the same way; the agent names the step, the tool, the error and what it tried. Every step can
be run again. The list flow, the connections, the flows and the app push all check what exists before they
change anything.
