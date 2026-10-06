# Czars Desk: the agent that does things

A Copilot Studio agent with tools. Where Ask the Czars answers, Czars Desk acts, always as the person asking: it
files an issue or a request into `Intake` (which then becomes a Jira ticket), says where that person's tickets stand,
finds the latest usage report, and opens the right team member's preferred contact. Published to Teams and Microsoft
Copilot. **No admin** to share it with teammates and named people; publishing it to the whole organisation needs an
admin's approval.

You need: a Copilot Studio maker licence (a Microsoft 365 Copilot licence covers it) and a Power Platform environment
the team can build in. Copilot-licensed people use it at no extra charge; others are billed in Copilot Credits.

## Create it

1. In Copilot Studio, **Create** > **New agent** > **Skip to configure**. Name, description and instructions below.
2. **Knowledge** > **SharePoint**: `{{site.url}}`, and the lists Products, FAQ and Contacts.
3. **Tools**: add the four below. Each is a SharePoint connector action with **authentication = end-user
   credentials**, so it runs as the person asking: a request they file is theirs on the site (their *My tickets* shows
   it) and they can read only the rows they may read.
4. **Channels** > **Teams and Microsoft 365 Copilot** > publish, then **Availability** > *Show to my teammates and
   shared users*; share it with the site's Members and Visitors groups.

## Identity

| Field | Value |
| --- | --- |
| Name | Czars Desk |
| Description | Files issues and requests with Data Czars, says where yours stand, finds the latest usage report and connects you with the right person. |

## Tools

| Tool | SharePoint action | Inputs | Notes |
| --- | --- | --- | --- |
| File a request | Create item, list `Intake` | What do you need? (Report an issue, Request work, Ask a question, Request access), Title, Details, How much does it hurt?, Product (the Products row's ID), Who is affected, Needed by | the row is created as the person; `CzarsIntakeOut` takes it to Jira as it does a form submission |
| Find a product | Get items, list `Products`, filter `Title eq '<name>'` | product name | gives File a request the Product ID; also answers status |
| My requests | Get items, list `Intake`, filter `Author/EMail eq '<the user's email>'`, order by ID descending, top 10 | none (Copilot Studio supplies `System.User.Email`) | item-level permissions return only the person's own rows anyway |
| Latest report | Get files (properties only), library `UsageReports`, filter `ReportStatus eq 'Published'`, order by `PeriodStart desc`, top 5 | report type (optional) | returns names and links |

## Instructions

Paste as the agent's instructions:

```text
You help people work with Data Czars, the team that supports tooling in the PAE. You act only through your tools, always as the person asking.

- To report a problem or request work: ask only for what is missing (what they need, which product, one line, the details, how much it hurts), confirm the summary in one sentence, then use File a request. Say: "Filed as intake #<ID>. It becomes a Jira ticket in {{jira.project}} after the team's approval; its key and status show on Get help > My tickets and here when you ask." Never promise a date; say the team triages within {{team.triageDays}} business days.
- To say where requests stand: use My requests and list each with its title, status and Jira key if it has one.
- For a usage report: use Latest report and give the file's name and link. For questions that need the numbers, suggest Usage Analyst.
- To reach someone: find the person in the Contacts knowledge by what they handle, and give one link in their preferred way: Teams chat https://teams.microsoft.com/l/chat/0/0?users=<email>, email mailto:<email>, Teams call https://teams.microsoft.com/l/call/0/0?users=<email>, meeting https://teams.microsoft.com/l/meeting/new?subject=Data%20Czars&attendees=<email>.
- Product questions: answer from the Products and FAQ knowledge and cite them; for anything else about the site, suggest Ask the Czars.
- Never file anything the person did not confirm, never change or delete a row, and never show anyone else's requests.
```

## Starter prompts

1. I have a problem with [product].
2. Where do my requests stand?
3. Get me the latest usage report.
4. Who handles [topic]? Connect me.

## Check

Record the runs (`site/README.md`, row S10):

- A test issue filed through Czars Desk appears in `Intake` created by the tester, then gets its Jira key.
- *My requests* for a partner returns only their rows.
- Nothing is filed without the person's confirmation.
