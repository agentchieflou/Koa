# The site's lists

Generated from `site/lists.json` by `python site/provision.py docs`; `tests/test_site.py` fails when this page and
the spec disagree, so edit the spec and regenerate rather than editing here.

Every list is made by one site script (`python site/provision.py scripts`), applied in this order because a
lookup column needs its target list to exist first. A choice column marked *from the scan* also gets the values
the scans found (`site/local/context.json`), ahead of the ones listed. The **Copilot fallback** under each list is
for a tenant where neither the provisioning flow nor the console can run: Copilot in SharePoint creates the
columns it supports, and the rest is done by hand as the list says.

## 1. Products

Every product Data Czars supports in the PAE: one row per product, with its state, how to start and where its docs are. Intake and the agent route by it. A list, 20 script actions, 0 tracked starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `Summary` | Summary | multiple lines of plain text | One or two sentences: what the product does for the person using it. |
| `Category` | Category | choice | from the scan (`products[].category`), then Other; required |
| `SupportLevel` | Support | choice | Supported, Preview, Deprecated, Retired (default Supported); required; Supported: we fix it. Preview: we fix it, it still changes. Deprecated: plan to move off it. |
| `Status` | Status | choice | Operational, Degraded, Maintenance, Down (default Operational); required |
| `CurrentVersion` | Current version | single line of text |  |
| `HowToStart` | How to start | single line of text | One sentence or one command, exactly as documented. |
| `DocsLink` | Docs | hyperlink |  |
| `RepoLink` | Repository | hyperlink |  |
| `JiraComponent` | Jira component | single line of text | The component an issue with this product is filed under. |
| `ProductOwner` | Owner | person |  |
| `Featured` | Featured | yes/no |  |
| `SortOrder` | Sort order | number |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `LinkTitle`, `Category`, `SupportLevel`, `Status`, `CurrentVersion`, `JiraComponent`, `ProductOwner` | list |
| Catalog | `Title`, `Summary`, `Category`, `SupportLevel`, `HowToStart`, `DocsLink`, `RepoLink`, `ProductOwner` | gallery, `formatting/products-catalog.json` |
| Status | `Title`, `Status`, `CurrentVersion` | gallery, `formatting/products-status.json` |
| Featured | `Title`, `Summary`, `Category`, `SupportLevel`, `HowToStart`, `DocsLink`, `RepoLink`, `ProductOwner` | gallery, `formatting/products-catalog.json` |

Column formatting: `Status` with `formatting/product-status.json`, `SupportLevel` with `formatting/support-level.json`.

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "Products" with the description "Every product Data Czars supports in the PAE: one row per product, with its state, how to start and where its docs are. Intake and the agent route by it."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- Summary: multiple lines of plain text.
- Category: choice with the choices Other, required.
- SupportLevel: choice with the choices Supported, Preview, Deprecated, Retired (default Supported), required.
- Status: choice with the choices Operational, Degraded, Maintenance, Down (default Operational), required.
- CurrentVersion: single line of text.
- HowToStart: single line of text.
- DocsLink: hyperlink.
- RepoLink: hyperlink.
- JiraComponent: single line of text.
- Featured: yes/no.
- SortOrder: number.
Propose the structure first and wait for my go-ahead before you create it.
```

Then add by hand `ProductOwner` (person); add the scanned values to `Category`; rename each column to its *Shown as* name (the internal name stays); paste each column formatter in **Format this column** > **Advanced mode**; create the views above and paste each view's formatter in **Format current view** > **Advanced mode**.

## 2. Releases

One row per release of a supported product: what changed and what a user has to do about it. A list, 11 script actions, 0 tracked starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `Headline` | Headline | single line of text | required |
| `Product` | Product | choice | from the scan (`products[].name`), then Other |
| `ReleasedOn` | Released | date |  |
| `Kind` | Kind | choice | Feature, Fix, Breaking, Security, Notes (default Feature) |
| `ReleaseNotes` | Notes | multiple lines of plain text |  |
| `UpdateSteps` | What you need to do | multiple lines of plain text | Empty when users need to do nothing. |
| `MoreLink` | Link | hyperlink |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `LinkTitle`, `Headline`, `Product`, `Kind`, `ReleasedOn` | list, `formatting/releases.json` |
| Latest | `Title`, `Headline`, `Kind` | list, `formatting/releases.json` |

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "Releases" with the description "One row per release of a supported product: what changed and what a user has to do about it."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- Headline: single line of text, required.
- Product: choice with the choices Other.
- ReleasedOn: date.
- Kind: choice with the choices Feature, Fix, Breaking, Security, Notes (default Feature).
- ReleaseNotes: multiple lines of plain text.
- UpdateSteps: multiple lines of plain text.
- MoreLink: hyperlink.
Propose the structure first and wait for my go-ahead before you create it.
```

Then add the scanned values to `Product`; rename each column to its *Shown as* name (the internal name stays); create the views above and paste each view's formatter in **Format current view** > **Advanced mode**.

## 3. Intake

Everything people bring to Data Czars: issues with a supported product, requests for work, questions and access. Each row becomes a ticket on the team's Jira board, and its Jira key and status come back here. A list, 19 script actions, 0 tracked starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `IntakeType` | What do you need? | choice | Report an issue, Request work, Ask a question, Request access (default Report an issue); required |
| `Product` | Product | lookup | looks up Products |
| `Details` | Details | multiple lines of plain text | required; What you did, what you expected, what happened; or what you need and the decision it serves. |
| `Impact` | How much does it hurt? | choice | Blocking my work, Slowing me down, Minor (default Slowing me down) |
| `AffectedTeam` | Who is affected | single line of text |  |
| `NeededBy` | Needed by | date |  |
| `Status` | Status | choice | New, Sent to Jira, In progress, Waiting on you, Done, Declined (default New); required |
| `JiraKey` | Jira | single line of text |  |
| `JiraLink` | Jira link | hyperlink |  |
| `Owner` | Owner | person |  |
| `SyncNote` | Last sync | single line of text | What the Jira flow last did with this row, in its own words. |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `LinkTitle`, `IntakeType`, `Product`, `Status`, `JiraKey`, `JiraLink`, `Owner`, `Author`, `Created` | list |
| Mine | `Title`, `IntakeType`, `Product`, `Status`, `JiraKey`, `JiraLink`, `Created` | list, `formatting/intake-mine.json` |
| Triage | `LinkTitle`, `IntakeType`, `Product`, `Impact`, `NeededBy`, `Author`, `Status`, `SyncNote` | list |
| Open | `LinkTitle`, `IntakeType`, `Product`, `Status`, `JiraKey`, `JiraLink`, `Owner` | list |

Column formatting: `Status` with `formatting/intake-status.json`, `JiraKey` with `formatting/jira-key.json`.

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "Intake" with the description "Everything people bring to Data Czars: issues with a supported product, requests for work, questions and access. Each row becomes a ticket on the team's Jira board, and its Jira key and status come back here."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- IntakeType: choice with the choices Report an issue, Request work, Ask a question, Request access (default Report an issue), required.
- Details: multiple lines of plain text, required.
- Impact: choice with the choices Blocking my work, Slowing me down, Minor (default Slowing me down).
- AffectedTeam: single line of text.
- NeededBy: date.
- Status: choice with the choices New, Sent to Jira, In progress, Waiting on you, Done, Declined (default New), required.
- JiraKey: single line of text.
- JiraLink: hyperlink.
- SyncNote: single line of text.
Propose the structure first and wait for my go-ahead before you create it.
```

Then add by hand `Product` (lookup to Products), `Owner` (person); rename each column to its *Shown as* name (the internal name stays); paste each column formatter in **Format this column** > **Advanced mode**; create the views above and paste each view's formatter in **Format current view** > **Advanced mode**.

## 4. Links

Every place Data Czars works in, one row per link: Confluence, Bitbucket, Jira, Power BI, Teams and the rest. A list, 9 script actions, 0 tracked starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `Url` | Link | hyperlink | required |
| `Category` | Category | choice | Confluence, Bitbucket, Jira, Power BI, Teams, SharePoint, Docs, Other (default Other); required |
| `LinkDescription` | Description | single line of text |  |
| `ShownTo` | For | choice | Everyone, Members (default Everyone) |
| `SortOrder` | Sort order | number |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `LinkTitle`, `Url`, `Category`, `ShownTo` | list |
| By category | `Title`, `Url`, `Category`, `LinkDescription`, `ShownTo` | list, `formatting/links.json` |

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "Links" with the description "Every place Data Czars works in, one row per link: Confluence, Bitbucket, Jira, Power BI, Teams and the rest."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- Url: hyperlink, required.
- Category: choice with the choices Confluence, Bitbucket, Jira, Power BI, Teams, SharePoint, Docs, Other (default Other), required.
- LinkDescription: single line of text.
- ShownTo: choice with the choices Everyone, Members (default Everyone).
- SortOrder: number.
Propose the structure first and wait for my go-ahead before you create it.
```

Then rename each column to its *Shown as* name (the internal name stays); create the views above and paste each view's formatter in **Format current view** > **Advanced mode**.

## 5. Contacts

The Data Czars team, each with what to ask them about and how they prefer to be reached: a Teams chat, an email, a call or a meeting. A list, 12 script actions, 0 tracked starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `Email` | Email | single line of text | required |
| `Person` | Person | person |  |
| `Role` | Role | single line of text |  |
| `Topics` | Ask me about | single line of text |  |
| `PreferredMethod` | Preferred method | choice | Teams chat, Email, Teams call, Book a meeting (default Teams chat); required |
| `WorkingHours` | Working hours | single line of text |  |
| `ShownTo` | For | choice | Everyone, Members (default Everyone) |
| `SortOrder` | Sort order | number |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `LinkTitle`, `Role`, `Topics`, `PreferredMethod`, `Email`, `WorkingHours` | list |
| Cards | `Title`, `Email`, `Role`, `Topics`, `PreferredMethod`, `WorkingHours` | gallery, `formatting/contacts-cards.json` |

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "Contacts" with the description "The Data Czars team, each with what to ask them about and how they prefer to be reached: a Teams chat, an email, a call or a meeting."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- Email: single line of text, required.
- Role: single line of text.
- Topics: single line of text.
- PreferredMethod: choice with the choices Teams chat, Email, Teams call, Book a meeting (default Teams chat), required.
- WorkingHours: single line of text.
- ShownTo: choice with the choices Everyone, Members (default Everyone).
- SortOrder: number.
Propose the structure first and wait for my go-ahead before you create it.
```

Then add by hand `Person` (person); rename each column to its *Shown as* name (the internal name stays); create the views above and paste each view's formatter in **Format current view** > **Advanced mode**.

## 6. FAQ

Questions people ask Data Czars, answered once. The site agent answers from here first. A list, 8 script actions, 5 tracked starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `Answer` | Answer | multiple lines of plain text | required |
| `Topic` | Topic | choice | from the scan (`products[].name`), then Getting help, Usage reports, This site, Other (default Getting help) |
| `ShownTo` | For | choice | Everyone, Members (default Everyone) |
| `SortOrder` | Sort order | number |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `LinkTitle`, `Topic`, `ShownTo` | list |
| Everyone | `Title`, `Answer`, `Topic` | list, `formatting/faq.json` |

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "FAQ" with the description "Questions people ask Data Czars, answered once. The site agent answers from here first."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- Answer: multiple lines of plain text, required.
- Topic: choice with the choices Getting help, Usage reports, This site, Other (default Getting help).
- ShownTo: choice with the choices Everyone, Members (default Everyone).
- SortOrder: number.
Propose the structure first and wait for my go-ahead before you create it.
```

Then add the scanned values to `Topic`; rename each column to its *Shown as* name (the internal name stays); create the views above and paste each view's formatter in **Format current view** > **Advanced mode**.

## 7. Prompts

Prompts that work, for Microsoft 365 Copilot and the Data Czars agents: copy one, change the brackets, send it. A list, 8 script actions, 6 tracked starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `PromptText` | Prompt | multiple lines of plain text | required |
| `UseIn` | Use in | choice | Microsoft Copilot, Ask the Czars, Czars Desk, Usage Analyst, Copilot in SharePoint, Copilot in Excel (default Microsoft Copilot); required |
| `Purpose` | Purpose | single line of text |  |
| `SortOrder` | Sort order | number |  |

| View | Shows | Layout |
| --- | --- | --- |
| All Items | `LinkTitle`, `UseIn`, `Purpose` | list |
| Library | `Title`, `PromptText`, `UseIn`, `Purpose` | list, `formatting/prompts.json` |

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a list called "Prompts" with the description "Prompts that work, for Microsoft 365 Copilot and the Data Czars agents: copy one, change the brackets, send it."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- PromptText: multiple lines of plain text, required.
- UseIn: choice with the choices Microsoft Copilot, Ask the Czars, Czars Desk, Usage Analyst, Copilot in SharePoint, Copilot in Excel (default Microsoft Copilot), required.
- Purpose: single line of text.
- SortOrder: number.
Propose the structure first and wait for my go-ahead before you create it.
```

Then rename each column to its *Shown as* name (the internal name stays); create the views above and paste each view's formatter in **Format current view** > **Advanced mode**.

## 8. UsageReports

The reports the usage tool publishes, for members of this site to read and download. Every file carries its report type, period and status. A document library, 12 script actions, 0 tracked starter rows.

| Column | Shown as | Type | Notes |
| --- | --- | --- | --- |
| `ReportType` | Report | choice | from the scan (`usageTool.reportTypes[].name`), then Usage report; Set from the folder the report lands in. |
| `PeriodStart` | Period | date | The first day the report covers; set from the folder. |
| `PeriodType` | Period type | choice | Daily, Weekly, Monthly, Quarterly, Ad hoc (default Monthly) |
| `Scope` | Covers | single line of text |  |
| `ToolVersion` | Usage tool version | single line of text |  |
| `ReportStatus` | Status | choice | Published, Draft, Superseded (default Published) |

| View | Shows | Layout |
| --- | --- | --- |
| All Documents | `DocIcon`, `LinkFilename`, `ReportType`, `PeriodStart`, `PeriodType`, `ReportStatus`, `Modified` | list |
| Latest | `DocIcon`, `LinkFilename`, `ReportType`, `PeriodStart`, `Scope` | list, `formatting/reports.json` |
| By report | `DocIcon`, `LinkFilename`, `PeriodStart`, `Scope`, `ReportStatus` | list |
| Drafts | `DocIcon`, `LinkFilename`, `ReportType`, `PeriodStart`, `Modified` | list |

**Copilot fallback.** In Copilot in SharePoint on the site, paste:

```text
Create a document library called "UsageReports" with the description "The reports the usage tool publishes, for members of this site to read and download. Every file carries its report type, period and status."
Add these columns. Name each one exactly as written here, with no spaces, and add nothing else:
- ReportType: choice with the choices Usage report.
- PeriodStart: date.
- PeriodType: choice with the choices Daily, Weekly, Monthly, Quarterly, Ad hoc (default Monthly).
- Scope: single line of text.
- ToolVersion: single line of text.
- ReportStatus: choice with the choices Published, Draft, Superseded (default Published).
Propose the structure first and wait for my go-ahead before you create it.
```

Then add the scanned values to `ReportType`; rename each column to its *Shown as* name (the internal name stays); create the views above and paste each view's formatter in **Format current view** > **Advanced mode**.
