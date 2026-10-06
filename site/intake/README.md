# Intake to Jira, and the usage reports' landing

Two pieces of plumbing behind the site: every request raised on **Get help** (or through Czars Desk) becomes a ticket
on the team's Jira board and its key and status come back to the row; and every report the usage tool produces lands
in the `UsageReports` library tagged with its type and period.

## Intake to Jira

### Why through the laptop

The team's Jira is inside the bank's network. Power Automate's Jira connector is Premium and does not reach a Jira
Server or Data Center behind a firewall; doing that needs a custom connector and an on-premises data gateway that IT
installs. Prefilled create-issue links were switched off in Jira 9. A Jira mail handler needs a Jira administrator and
never returns the new key. The laptop already reaches Jira: `ad-jira create` (this-next-please) writes with the token
pncli keeps, and every write waits for the operator's one approval on the desk or the phone. So the site hands each
request to the laptop and takes the answer back, through two Standard-connector flows and the operator's OneDrive,
which is the same outbox-and-inbox pattern FleetAgent uses.

```
Get help form / Czars Desk -> Intake row (Status New)
  CzarsIntakeOut (flow, every minute): writes <OneDrive>/DataCzars/intake/intake-<id>.json; row says "Waiting to be filed"
laptop: python site/intake/intake.py file --all
  ad-jira create  (project, type, component and labels from the scanned facts; one approval each, desk or phone)
  writes <OneDrive>/DataCzars/results/<id>-<time>.json and ledger.json
  CzarsIntakeBack (flow, every five minutes): merges the key, link, status and a sentence into the row
laptop: python site/intake/intake.py sync      (any time: Jira's status category -> Sent to Jira, In progress, Done)
```

| Intake says | Jira issue type | From the context |
| --- | --- | --- |
| Report an issue | `jira.issueTypes.issue` | the data-czars scan; `Bug` when the project uses it |
| Request work, Ask a question, Request access | `jira.issueTypes.request`, `.question`, `.access` | `jira_issue_type` in data-czars' `AGENTS.md` |

The product picked on the form gives the component (`jiraComponent` in the scanned products); `jira.labels` (with
`sharepoint-intake`) marks every ticket that came from the site.

### Set it up (once)

1. **The folders.** In the operator's OneDrive: `DataCzars/intake` and `DataCzars/results`. On the laptop they are
   `%OneDriveCommercial%\DataCzars\...`, the folder `intake.py` uses by default.
2. **The results folder's id.** With the FlowAgent tools, or in any flow's folder picker, find the id of
   `DataCzars/results` (the FleetAgent build's step 05 finds the outbox's the same way).
3. **The flows.** `python site/provision.py flows --results-folder-id <id>` writes `site/out/CzarsIntakeOut.json`,
   `CzarsIntakeBack.json` and `CzarsTagReports.json`. A Copilot agent creates and turns them on with the
   `build-czars-site` skill; they use only the SharePoint and OneDrive for Business connectors (Standard).
4. **A first ticket.** Submit a test issue on Get help; within a minute `intake-<id>.json` appears in the folder.
   `python site/intake/intake.py file <id> --dry-run` shows what would be filed; without `--dry-run` it asks for the
   approval and files it. Within five minutes the row shows the key.

### Run it

- `python site/intake/intake.py list` shows what is waiting; `file --all` files it (one approval each);
  `sync` refreshes the statuses. The fleet's data-czars agent can run the same commands as part of its day, and the
  approvals reach the operator wherever FleetAgent does.
- A row the team declines: set **Status** to *Declined* on the site and say why in **Last sync**; `sync` never
  reopens it.

### Other routes

| Route | When | What it takes | The key comes back |
| --- | --- | --- | --- |
| **A. Through the laptop** (above) | now | nothing new: OneDrive, two Standard flows, `ad-jira` | yes |
| **B. Jira custom connector** | when IT can install an on-premises data gateway | a Premium licence for the flow's owner, a custom connector for the Jira REST API, the gateway | yes, from the cloud, laptop off |
| **C. Jira mail handler** | when a Jira admin sets one up | an Office 365 Outlook flow sends a structured email; Exchange needs an OAuth app registration on Jira's side | no |
| **D. Jira Service Management portal** | if the team runs a JSM project | portal links prefilled with summary and description (2,048 characters at most) | no |

Route B keeps the same `Intake` list, form and pages: only `CzarsIntakeOut` changes, from writing a file to calling
the connector.

## The usage reports' landing

The usage tool's reports land in the `UsageReports` library, one folder per report type and one per month inside it:

```
UsageReports/<report type>/<yyyy-mm>/<file>
```

1. **Getting the files there.** On the machine that runs the usage tool, open the library on the site > **Add
   shortcut to My files** (Microsoft's recommended way over **Sync**). The library then appears under OneDrive in File
   Explorer. Have the tool (or the step after it) write each finished report to its folder there, whole: write it
   elsewhere first and move it in, so OneDrive never uploads half a file.
2. **Tagging them.** `CzarsTagReports` runs every hour: any report without a type takes its type and period from its
   folder (`Report` = the type folder, `Period` = the first of the month, `Status` = Published). Library settings >
   **Column default value settings** on each type folder sets the type even for a file dragged in by hand.
3. **Nothing in the library is required.** A synced library with required columns, check-out or validation goes
   read-only, so every column is optional and the flow fills them.

Autofill columns (Copilot in SharePoint) can read a report's contents instead, for English xlsx, csv and pdf files,
but they do not re-tag a file that is overwritten; the folder is the more dependable signal.

## What only the tenant can prove

`site/README.md` rows S11 to S13: a form submission reaches the laptop as a file; a result file updates its row; a
report copied into a dated folder is tagged within the hour.
