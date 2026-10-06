# Links

**URL:** `SitePages/Links.aspx`. **For:** everyone; links marked *Members* lead to places only the team can open.
**Design:** the canvas artboard *Links*.

Every place Data Czars works, in one list: the Confluence spaces, the Bitbucket repositories, the Jira board, the
Power BI workspaces, the Teams channels. The data-czars, usage_tool and Microsoft 365 Copilot scans fill it; members
add a row when a place is missing.

## Build it with Copilot

From any page, open **Copilot** and ask it to create a page, then paste (`site/out/pages/links.md` has it filled in):

```text
Create a page called "Links" for the Data Czars site. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

Title area: Image layout, topic header "Where we work", title "Links", and the description "Every place Data Czars works: Confluence, Bitbucket, Jira, Power BI and Teams."

1. One-column section, no background. A Quick links web part, Button layout, with icons: Jira board ({{jira.boardUrl}}), Get help (Get-help.aspx), Contact (Contact.aspx).
2. One-column section, no background. Heading "All links", then a List web part.
3. One-column section, Neutral background. A Text web part: "Missing a link? Members add a row to the Links list; everyone else, tell us on Get help."
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| title | Image layout | title area | background `assets/title-links.png` |
| 1 | One column, none | Quick links, Button | icons on |
| 2 | One column, none | List | `Links`, view `By category`; command bar on, so people can search |
| 3 | One column, Neutral | Text | |

## Words

All of it is in the prompt. The list groups by category with an icon for each; a *Members* tag marks links to places
only the team can open (source code, internal runbooks).

## Finish by hand

1. Check every row the scans added: the link opens, the description is one sentence, the category is right.
2. Publish, and set the page description: "Every place Data Czars works: Confluence, Bitbucket, Jira, Power BI, Teams."

## Check

- Every link opens. Ask the site agent "Where is the Confluence space?": it answers with the row's link.
