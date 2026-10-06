# Data Czars in Microsoft Copilot

The site is built so Copilot can stand in for it: everything a person can find on a page, an agent can find, cite and
act on. Three agents, one Teams wiring, and the Copilot features that make the team's routine run on its own. Every
part a site owner or the team can set up without a tenant admin is marked **no admin**; the four things only an admin
can switch on are at the end, as one request to IT.

`python site/provision.py pages` fills the double-braced facts in these files from the scans and writes them, ready to
paste, to `site/out/agents/`.

## The three agents

| Agent | What it is for | Built in | Lives in | Admin |
| --- | --- | --- | --- | --- |
| **Ask the Czars** (`ask-the-czars.md`) | answers about products, status, help, links and people, from the site, citing every answer | SharePoint (a site agent) | the site header, Microsoft Copilot, Teams chats and channels | no admin |
| **Usage Analyst** (`usage-analyst.md`) | answers questions about usage with the numbers, reading the report files themselves with code interpreter | Agent Builder in Microsoft Copilot | Microsoft Copilot, Teams | no admin |
| **Czars Desk** (`czars-desk.md`) | does things: files an issue as the person asking, says where their tickets stand, finds the latest report, opens the right person's preferred contact | Copilot Studio | Microsoft Copilot, Teams | no admin to share with teammates; org-wide needs approval |

Why three and not one: a SharePoint site agent reads up to 20 sources of the site, lists included, but takes no
actions; Agent Builder takes no actions either, but reads files with code interpreter; only Copilot Studio calls
tools. Each agent does the one thing its builder is best at, and each says when to use the other two.

## Teams (no admin)

1. **The team's channel.** Add tabs: the site's Home, the `Intake` list (view Triage), the `UsageReports` library.
2. **Ask the Czars in the channel.** In SharePoint, the agent's **...** > **Copy link for Teams**; paste it in the
   channel and in the team's chat; anyone there can @mention it.
3. **New intake, posted.** A Workflows flow (Standard connectors): *When an item is created* in `Intake` > *Post card
   in a chat or channel* with the title, type, product, impact and a link to the row. Members see every request the
   moment it lands, before it is filed in Jira.
4. **Reports, announced.** A second flow: *When a file is created (properties only)* in `UsageReports` > post the file's
   name and link to the channel, so the month's reports announce themselves.

## Copilot features the team uses

- **Scheduled prompts** (Microsoft Copilot, per person): Monday "@Czars Desk what came in last week and where does it
  stand?"; the first working day of the month "@Usage Analyst what changed in the new usage reports?".
- **Prompt Gallery**: the `Prompts` list's prompts, saved and shared to the team, so they appear in everyone's Copilot.
- **Copilot Notebooks** for a piece of work: the product's docs, its Jira emails and the relevant reports in one
  place, with Copilot answering across them.
- **Researcher and Analyst** (included with Copilot): Analyst over a downloaded usage report when a question needs
  more than Usage Analyst's charts.

## One request to IT (admin only)

Each of these widens what Copilot can see or reach. None is needed for the site to work.

| Ask | What it adds | Where |
| --- | --- | --- |
| Copilot connectors for **Jira Data Center** and **Confluence on-premises** | Copilot and every agent can search and cite Jira issues and Confluence pages | Microsoft 365 admin center > Copilot > Connectors; needs the Graph connector agent on a Windows server inside the network and a plugin in Jira and Confluence (Jira DC 8.10 to 10.5.1, Confluence 8.0 or later) |
| Publish **Czars Desk** to the whole organisation | anyone at the bank finds it in the Agent Store | Microsoft 365 admin center > Agents > Requests |
| A **Jira custom connector** with an on-premises data gateway | Intake files tickets straight from the cloud, without the laptop (`site/intake/README.md`, route B) | Power Platform admin center; the gateway is installed by IT |
| **Channel Agent** with the Atlassian MCP server, where Jira or Confluence is Cloud | the team's channel agent reads and writes Jira and Confluence | Teams admin center |

## Check

Each agent's file ends with its own check; record the runs as `site/README.md` says (rows S8 to S10).
