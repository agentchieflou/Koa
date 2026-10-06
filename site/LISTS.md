# The site's lists

Generated from `site/lists.json` by `python site/provision.py docs`; `tests/test_site.py` fails when this page and
the spec disagree, so edit the spec and regenerate rather than editing here.

Every list is made by one site script (`python site/provision.py scripts`), applied in this order because a
lookup column needs its target list to exist first. The **Copilot fallback** under each list is for a tenant
where neither the provisioning flow nor the console can run: Copilot in SharePoint creates the columns it
supports, and the rest is done by hand as the list says.

## 1. Tools

Every tool Data Czars builds and supports: one row per tool. Drives the catalog, the status strip and the featured cards. A list, 19 script actions, 10 starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `Summary` | Summary | multiple lines of plain text | One or two sentences: what the tool does for the person using it. |
| `Category` | Category | choice | Agent platform, Data and BI, Testing and UAT, Document AI, Developer experience, Mobile; required |
| `Maturity` | Maturity | choice | GA, Preview, Lab, Retired (default Preview); required; GA: supported for everyone. Preview: supported, still changing. Lab: try it, no promises. |
| `Status` | Status | choice | Operational, Degraded, Maintenance, Down (default Operational); required |
| `CurrentVersion` | Current version | single line of text |  |
| `StartCommand` | Start command | single line of text | The one command that starts the tool, as typed. |
| `DocsLink` | Docs | hyperlink |  |
| `RepoLink` | Repository | hyperlink |  |
| `ToolOwner` | Owner | person |  |
| `Featured` | Featured | yes/no |  |
| `SortOrder` | Sort order | number |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `LinkTitle`, `Category`, `Maturity`, `Status`, `CurrentVersion`, `ToolOwner` | list |
| Catalog | `Title`, `Summary`, `Category`, `Maturity`, `StartCommand`, `DocsLink`, `RepoLink`, `ToolOwner` | gallery, `formatting/tools-catalog.json` |
| Status | `Title`, `Status`, `CurrentVersion` | gallery, `formatting/tools-status.json` |
| Featured | `Title`, `Summary`, `Category`, `Maturity`, `StartCommand`, `DocsLink`, `RepoLink`, `ToolOwner` | gallery, `formatting/tools-catalog.json` |

Column formatting: `Status` with `formatting/tool-status.json`, `Maturity` with `formatting/maturity.json`.

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "Tools" with the description "Every tool Data Czars builds and supports: one row per tool. Drives the catalog, the status strip and the featured cards."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- Summary: multiple lines of plain text.
- Category: choice with the choices Agent platform, Data and BI, Testing and UAT, Document AI, Developer experience, Mobile, required.
- Maturity: choice with the choices GA, Preview, Lab, Retired (default Preview), required.
- Status: choice with the choices Operational, Degraded, Maintenance, Down (default Operational), required.
- CurrentVersion: single line of text.
- StartCommand: single line of text.
- DocsLink: hyperlink.
- RepoLink: hyperlink.
- Featured: yes/no.
- SortOrder: number.
Propose the structure first and wait for my go-ahead before you create it.
```

Then add by hand `ToolOwner` (person); rename each column to its *Shown as* name (the internal name stays); paste each column formatter in **Format this column** > **Advanced mode**; create the views above and paste each view's formatter in **Format current view** > **Advanced mode**.

## 2. Releases

One row per release of a tool: what changed and whether an update needs more than the standard commands. A list, 11 script actions, 4 starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `Headline` | Headline | single line of text | required |
| `Tool` | Tool | lookup | looks up Tools |
| `ReleasedOn` | Released | date |  |
| `Kind` | Kind | choice | Feature, Fix, Breaking, Security, Notes (default Feature) |
| `ReleaseNotes` | Notes | multiple lines of plain text |  |
| `UpdateSteps` | On update | multiple lines of plain text | What an update needs beyond ad-update and a new Copilot chat. Empty when nothing. |
| `MoreLink` | Link | hyperlink |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `LinkTitle`, `Headline`, `Tool`, `Kind`, `ReleasedOn` | list, `formatting/releases.json` |
| Latest | `Title`, `Headline`, `Kind` | list, `formatting/releases.json` |

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "Releases" with the description "One row per release of a tool: what changed and whether an update needs more than the standard commands."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- Headline: single line of text, required.
- ReleasedOn: date.
- Kind: choice with the choices Feature, Fix, Breaking, Security, Notes (default Feature).
- ReleaseNotes: multiple lines of plain text.
- UpdateSteps: multiple lines of plain text.
- MoreLink: hyperlink.
Propose the structure first and wait for my go-ahead before you create it.
```

Then add by hand `Tool` (lookup to Tools); rename each column to its *Shown as* name (the internal name stays); create the views above and paste each view's formatter in **Format current view** > **Advanced mode**.

## 3. Requests

Work requested from Data Czars by partners across the bank: one row per request, triaged within the promised days. A list, 15 script actions, 0 starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `RequestType` | Request type | choice | New report or dashboard, Data pull, Automation or agent, Tool access, UAT support, Consultation, Problem with a tool; required |
| `Details` | Details | multiple lines of plain text | required; What you need and what decision it serves. |
| `UsedBy` | Who will use it | single line of text |  |
| `RequesterTeam` | Your team | single line of text |  |
| `NeededBy` | Needed by | date |  |
| `Benefit` | Benefit | choice | High, Medium, Low (default Medium) |
| `Status` | Status | choice | New, Triage, Accepted, In progress, Blocked, Done, Declined (default New); required |
| `Owner` | Owner | person |  |
| `JiraKey` | Jira | single line of text |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `LinkTitle`, `RequestType`, `Status`, `Owner`, `NeededBy`, `Author`, `JiraKey` | list |
| Mine | `LinkTitle`, `RequestType`, `Status`, `Owner`, `NeededBy` | list |
| Triage | `LinkTitle`, `RequestType`, `Benefit`, `NeededBy`, `Author`, `RequesterTeam`, `Status` | list |

Column formatting: `Status` with `formatting/request-status.json`.

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "Requests" with the description "Work requested from Data Czars by partners across the bank: one row per request, triaged within the promised days."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- RequestType: choice with the choices New report or dashboard, Data pull, Automation or agent, Tool access, UAT support, Consultation, Problem with a tool, required.
- Details: multiple lines of plain text, required.
- UsedBy: single line of text.
- RequesterTeam: single line of text.
- NeededBy: date.
- Benefit: choice with the choices High, Medium, Low (default Medium).
- Status: choice with the choices New, Triage, Accepted, In progress, Blocked, Done, Declined (default New), required.
- JiraKey: single line of text.
Propose the structure first and wait for my go-ahead before you create it.
```

Then add by hand `Owner` (person); rename each column to its *Shown as* name (the internal name stays); paste each column formatter in **Format this column** > **Advanced mode**.

## 4. Roadmap

What Data Czars is building now, next and later. One row per item; the lane is the promise. A list, 12 script actions, 6 starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `Lane` | Lane | choice | Now, Next, Later, Shipped (default Next); required |
| `Tool` | Tool | lookup | looks up Tools |
| `Summary` | Summary | multiple lines of plain text |  |
| `Ticket` | Ticket | single line of text | The issue, epic or plan the item comes from. |
| `MoreLink` | Link | hyperlink |  |
| `SortOrder` | Sort order | number |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `LinkTitle`, `Lane`, `Tool`, `Ticket` | list |
| Now | `Title`, `Tool`, `Ticket`, `Summary` | list, `formatting/roadmap.json` |
| Next | `Title`, `Tool`, `Ticket`, `Summary` | list, `formatting/roadmap.json` |
| Later | `Title`, `Tool`, `Ticket`, `Summary` | list, `formatting/roadmap.json` |

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "Roadmap" with the description "What Data Czars is building now, next and later. One row per item; the lane is the promise."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- Lane: choice with the choices Now, Next, Later, Shipped (default Next), required.
- Summary: multiple lines of plain text.
- Ticket: single line of text.
- MoreLink: hyperlink.
- SortOrder: number.
Propose the structure first and wait for my go-ahead before you create it.
```

Then add by hand `Tool` (lookup to Tools); rename each column to its *Shown as* name (the internal name stays); create the views above and paste each view's formatter in **Format current view** > **Advanced mode**.

## 5. Decisions

The decision log: what Data Czars decided, why, and what it costs. One row per decision; superseded rows stay. A list, 13 script actions, 5 starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `DecisionNo` | No. | single line of text | required |
| `DecisionStatus` | Status | choice | Proposed, Accepted, Superseded, Rejected (default Proposed); required |
| `DecidedOn` | Decided | date |  |
| `DecisionContext` | Context | multiple lines of plain text |  |
| `DecisionText` | Decision | multiple lines of plain text |  |
| `Consequences` | Consequences | multiple lines of plain text |  |
| `SourceRef` | Source | single line of text |  |
| `MoreLink` | Link | hyperlink |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `DecisionNo`, `LinkTitle`, `DecisionStatus`, `DecidedOn`, `SourceRef` | list |
| Log | `DecisionNo`, `Title`, `DecisionStatus`, `SourceRef` | list, `formatting/decisions.json` |

Column formatting: `DecisionStatus` with `formatting/decision-status.json`.

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "Decisions" with the description "The decision log: what Data Czars decided, why, and what it costs. One row per decision; superseded rows stay."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- DecisionNo: single line of text, required.
- DecisionStatus: choice with the choices Proposed, Accepted, Superseded, Rejected (default Proposed), required.
- DecidedOn: date.
- DecisionContext: multiple lines of plain text.
- DecisionText: multiple lines of plain text.
- Consequences: multiple lines of plain text.
- SourceRef: single line of text.
- MoreLink: hyperlink.
Propose the structure first and wait for my go-ahead before you create it.
```

Then rename each column to its *Shown as* name (the internal name stays); paste each column formatter in **Format this column** > **Advanced mode**; create the views above and paste each view's formatter in **Format current view** > **Advanced mode**.

## 6. Glossary

The words Data Czars uses, defined once. The site agent answers from here first. A list, 7 script actions, 12 starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `Definition` | Definition | multiple lines of plain text | required |
| `SeeAlso` | See also | single line of text |  |
| `MoreLink` | Link | hyperlink |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `LinkTitle`, `Definition`, `SeeAlso` | list |
| A to Z | `Title`, `Definition` | list, `formatting/glossary.json` |

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "Glossary" with the description "The words Data Czars uses, defined once. The site agent answers from here first."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- Definition: multiple lines of plain text, required.
- SeeAlso: single line of text.
- MoreLink: hyperlink.
Propose the structure first and wait for my go-ahead before you create it.
```

Then rename each column to its *Shown as* name (the internal name stays); create the views above and paste each view's formatter in **Format current view** > **Advanced mode**.

## 7. FAQ

Questions people ask Data Czars, answered once. Partners see the Partners rows; members see all. A list, 9 script actions, 7 starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `Answer` | Answer | multiple lines of plain text | required |
| `Topic` | Topic | choice | Getting started, The fleet, Power BI, Data, Requests, This site |
| `ShownTo` | Shown to | choice | Partners, Members (default Partners) |
| `SortOrder` | Sort order | number |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `LinkTitle`, `Topic`, `ShownTo` | list |
| Partners | `Title`, `Answer` | list, `formatting/faq.json` |
| Members | `Title`, `Answer` | list, `formatting/faq.json` |

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "FAQ" with the description "Questions people ask Data Czars, answered once. Partners see the Partners rows; members see all."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- Answer: multiple lines of plain text, required.
- Topic: choice with the choices Getting started, The fleet, Power BI, Data, Requests, This site.
- ShownTo: choice with the choices Partners, Members (default Partners).
- SortOrder: number.
Propose the structure first and wait for my go-ahead before you create it.
```

Then rename each column to its *Shown as* name (the internal name stays); create the views above and paste each view's formatter in **Format current view** > **Advanced mode**.

## 8. Metrics

The numbers on Home and Impact, one row per measure, written by a scheduled flow. Every number carries its method. A list, 12 script actions, 4 starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `MetricValue` | Value | single line of text | required |
| `MetricLabel` | Label | single line of text | required |
| `MetricWindow` | Window | single line of text |  |
| `Definition` | Definition | multiple lines of plain text |  |
| `SourceRef` | Source | single line of text |  |
| `RefreshedOn` | Refreshed | date |  |
| `SortOrder` | Sort order | number |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `LinkTitle`, `MetricValue`, `MetricWindow`, `RefreshedOn` | list |
| Tiles | `Title`, `MetricValue`, `MetricLabel`, `MetricWindow` | gallery, `formatting/metrics-tiles.json` |
| Method | `Title`, `Definition`, `SourceRef`, `RefreshedOn` | list |

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "Metrics" with the description "The numbers on Home and Impact, one row per measure, written by a scheduled flow. Every number carries its method."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- MetricValue: single line of text, required.
- MetricLabel: single line of text, required.
- MetricWindow: single line of text.
- Definition: multiple lines of plain text.
- SourceRef: single line of text.
- RefreshedOn: date.
- SortOrder: number.
Propose the structure first and wait for my go-ahead before you create it.
```

Then rename each column to its *Shown as* name (the internal name stays); create the views above and paste each view's formatter in **Format current view** > **Advanced mode**.

## 9. LearningPaths

The 101, 201 and 301 paths: one row per module, in order. A list, 12 script actions, 12 starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `PathLevel` | Path | choice | 101, 201, 301; required |
| `StepNo` | Step | number | required |
| `ModuleFormat` | Format | choice | Guide, Video, Workshop (default Guide) |
| `Tool` | Tool | lookup | looks up Tools |
| `Summary` | Summary | multiple lines of plain text |  |
| `MoreLink` | Link | hyperlink |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `LinkTitle`, `PathLevel`, `StepNo`, `ModuleFormat`, `Tool` | list |
| 101 | `Title`, `StepNo`, `ModuleFormat`, `MoreLink` | list, `formatting/learning-path.json` |
| 201 | `Title`, `StepNo`, `ModuleFormat`, `MoreLink` | list, `formatting/learning-path.json` |
| 301 | `Title`, `StepNo`, `ModuleFormat`, `MoreLink` | list, `formatting/learning-path.json` |

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "LearningPaths" with the description "The 101, 201 and 301 paths: one row per module, in order."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- PathLevel: choice with the choices 101, 201, 301, required.
- StepNo: number, required.
- ModuleFormat: choice with the choices Guide, Video, Workshop (default Guide).
- Summary: multiple lines of plain text.
- MoreLink: hyperlink.
Propose the structure first and wait for my go-ahead before you create it.
```

Then add by hand `Tool` (lookup to Tools); rename each column to its *Shown as* name (the internal name stays); create the views above and paste each view's formatter in **Format current view** > **Advanced mode**.

## 10. WhoToAsk

Who answers what: one row per topic, with a backup and the right place to ask. A list, 7 script actions, 8 starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `Contact` | Ask | person |  |
| `Backup` | Backup | person |  |
| `Channel` | Where | choice | Team channel, Office hours, Request work (default Team channel) |
| `Details` | Details | single line of text |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `LinkTitle`, `Contact`, `Backup`, `Channel` | list |

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "WhoToAsk" with the description "Who answers what: one row per topic, with a backup and the right place to ask."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- Channel: choice with the choices Team channel, Office hours, Request work (default Team channel).
- Details: single line of text.
Propose the structure first and wait for my go-ahead before you create it.
```

Then add by hand `Contact` (person), `Backup` (person); rename each column to its *Shown as* name (the internal name stays).

## 11. Onboarding

A new Czar's first day, week and month: one row per task, in order. A list, 8 script actions, 12 starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `Phase` | Phase | choice | Day one, Week one, Month one; required |
| `StepNo` | Step | number |  |
| `Category` | Category | choice | Access, Laptop, Reading, People, First task |
| `Details` | Details | multiple lines of plain text |  |
| `MoreLink` | Link | hyperlink |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `StepNo`, `LinkTitle`, `Phase`, `Category`, `MoreLink` | list |

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "Onboarding" with the description "A new Czar's first day, week and month: one row per task, in order."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- Phase: choice with the choices Day one, Week one, Month one, required.
- StepNo: number.
- Category: choice with the choices Access, Laptop, Reading, People, First task.
- Details: multiple lines of plain text.
- MoreLink: hyperlink.
Propose the structure first and wait for my go-ahead before you create it.
```

Then rename each column to its *Shown as* name (the internal name stays).

## 12. Guides

Guides, runbooks, standards, decks and recordings. Every file carries Kind, Tool, Review by and Owner, so the site agent can tell a current runbook from an old one. A document library, 11 script actions, 0 starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `Kind` | Kind | choice | Guide, Runbook, Reference, Standard, Recording, Deck, Template (default Guide); required |
| `Tool` | Tool | lookup | looks up Tools |
| `ReviewBy` | Review by | date |  |
| `DocOwner` | Owner | person |  |
| `ShownTo` | Shown to | choice | Partners, Members (default Partners) |

| View | Shows | Layout |
| --- | --- | --- |
| All Documents | `DocIcon`, `LinkFilename`, `Kind`, `Tool`, `ReviewBy`, `DocOwner`, `Modified` | list |
| Guides | `DocIcon`, `LinkFilename`, `Kind`, `Tool`, `ReviewBy` | list |
| Standards | `DocIcon`, `LinkFilename`, `ReviewBy`, `DocOwner` | list |
| Recordings | `DocIcon`, `LinkFilename`, `Tool`, `Modified` | list |

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a document library called "Guides" with the description "Guides, runbooks, standards, decks and recordings. Every file carries Kind, Tool, Review by and Owner, so the site agent can tell a current runbook from an old one."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- Kind: choice with the choices Guide, Runbook, Reference, Standard, Recording, Deck, Template (default Guide), required.
- ReviewBy: date.
- ShownTo: choice with the choices Partners, Members (default Partners).
Propose the structure first and wait for my go-ahead before you create it.
```

Then add by hand `Tool` (lookup to Tools), `DocOwner` (person); rename each column to its *Shown as* name (the internal name stays).
