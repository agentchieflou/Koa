# Building FleetAgent with a Copilot agent

This folder lets a GitHub Copilot agent drive the build of everything on the Microsoft 365 side, end to end:

- the five SharePoint lists, and the library that holds each operator's bridge folder, all readable by the site's
  Owners only;
- the flows: `FleetDecide`, which every operator's phone calls, and one copy of `FleetOutboxToLists` per operator,
  which reads only that operator's folder;
- the FleetAgent canvas app, built from the sources in `powerapp/src`.

Several operators share it: each runs their own fleet on their own laptop, and everyone sees one app. The build is
done once, by one of them. Then each operator connects their own laptop and phone with
[each-operator.md](each-operator.md), which takes about five minutes.

A GitHub Copilot agent prepares and checks everything; you do the browser work. The organisation blocks MCP
servers and agent plugins, so the agent never touches Power Automate, Power Apps or SharePoint itself: it writes the
files you import or paste, tells you exactly what to click, and checks what you paste back from a run or from Studio.
It stops and tells you when each click is due.

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

1. **A Copilot agent.** Either **VS Code** with GitHub Copilot, using Chat in **Agent** mode, or **GitHub Copilot
   CLI** (`npm install -g @github/copilot`, then `copilot` in the repository folder). Nothing to add to it: no
   plugin, no extension, no MCP server.
2. **Python 3.10 or later** on the laptop, and **Microsoft Edge** signed in with your work account.

That is all. You do not need the .NET SDK, `az login`, or any connection made ahead of time.

## 3. Start the build

In the repository folder, tell the agent:

> Build FleetAgent. Use the build-fleetagent skill.

The agent asks for your SharePoint site's address, the operators, and your Power Platform environment's name. It
records what is done in `build/out/state.json`, so if a session ends you can say the same sentence again and it
continues where it stopped.

## 4. What you do

The agent stops, tells you exactly what to click, and waits for you each time:

| When | You do | Time |
| --- | --- | --- |
| step 01 | give the environment's name, the SharePoint site's address and every operator's UPN. The site must be a team or communication site where all of you are **Owners**; cloud connections cannot reach a personal site's "My lists" | 2 min |
| step 02 | import `FleetProvisionLists.zip`, pick your SharePoint connection, run it once, and save its last action's output for the agent to check | 5 min |
| steps 03, 05 | import `FleetDecide.zip` and each `FleetOutboxToLists (<UPN>).zip`, picking connections (SharePoint, Office 365 Users, Power Apps Notification), and turn each flow on | 5 min |
| step 04 | create the blank app in Studio and change four settings (step 04 lists each click), then paste the Studio URL into the chat | 3 min |
| step 05 | change each operator's copy of `FleetOutboxToLists` to be owned by that operator (step 05 lists each click), so each copy runs on its owner's daily request limit | 3 min |
| step 06 | add the five lists and the `FleetDecide` flow through **Data** > **Add data**, then paste the app in thirteen pastes (the agent puts each one on your clipboard) and copy any error Studio shows back to the agent | 20 min |
| step 07 | paste the theme (optional), **Publish**, **Share** the app with the other operators, add them to `FleetDecide`'s run-only users, and save the app to your laptop once so the agent can mirror it | 5 min |
| after the build, each operator | add a shortcut to their own bridge folder, point their laptop's bridge at it, and open the app once on the phone ([each-operator.md](each-operator.md)) | 5 min |

The agent's part: the config, every file you import or paste, reading back each run's report and each Studio error,
every fix to the repository's sources and its tests, and the final check.

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

Each step ends in **Done**, **Waiting for you** (one of the clicks above), or **Blocked**. Blocked means the same
import or paste failed twice in the same way; the agent names the step, the file, the error and what it tried. Every
step can be run again: a package imported with **Update** replaces its flow, and the list flow changes nothing that
is already right. If your organisation refuses **Import Package (Legacy)** itself, each step names the hand-built
fallback (`flows/README.md`, `data/README.md`).

## Not yet measured

Only the tenant can prove these. Each reads *not yet measured* until someone has run it and recorded what they saw,
as `AGENTS.md` rule 7 says:

| Row | What | How to see it | Result |
| --- | --- | --- | --- |
| B1 | **Import Package (Legacy)** accepts the packages `prepare.py` writes (laid out as Power Automate exports one) | step 02: the import page lists the flow and asks for a SharePoint connection | not yet measured |
| B2 | `FleetDecide`'s Office 365 Users connection arrives as **Provided by run-only user** | step 03: **Run only users** shows it so; if not, the step sets it by hand | not yet measured |
| B3 | a `.msapp` saved from Studio carries the app as `Src/*.pa.yaml`, which `canvas-out` reads | step 07: `canvas-out` names every screen and component | not yet measured |
