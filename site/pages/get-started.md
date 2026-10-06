# Get started

**URL:** `SitePages/Get-started.aspx`. **For:** everyone new to the kernel, and anyone setting it up again.
**Design:** the canvas artboard *Get started*.

The page a person reads before their first notebook: what the kernel gives them, the access to request, the setup,
a first Spark session, which profile to pick, and what to do when it fails. Access, profiles and common errors are
lists filled from the data-czars scan and the team's Confluence pages (`site/prompts/confluence-page-facts.md`); the
setup steps and the first session come from the same places, so the page changes only when its purpose does.

## Build it with Copilot

From any page, open **Copilot** and ask it to create a page, then paste (`site/out/pages/get-started.md` has it filled
in):

```text
Create a page called "Get started" for the Data Czars site. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

Title area: Image layout, topic header "New to the kernel", title "Get started", and the description "{{kernel.summary}}"

1. Two-thirds left section, no background. Left: heading "What you get", then a Text web part: "{{kernel.buildsOn}} It adds {{kernel.includes}}, and its Spark sessions reach {{kernel.connectsTo}}." Right: heading "Before you start", a Text web part: "The kernel opens only once your access is granted. Request all of it in one go, then follow Set up.", and a Button web part "Get access" linking to Get-started.aspx#get-access.
2. One-column section, no background. Heading "Get access", a Text web part: "Request every entitlement marked Using the kernel. Ask for those marked Contributing code only if you will change the code.", then a List web part.
3. Two-thirds left section, Neutral background. Left: heading "Set up", then a Text web part with this numbered list:
   {{kernel.setupSteps|numbered}}
   Right: heading "Your first session", then a Text web part: "Open a new notebook on the {{kernel.name}} and run this cell to start Spark. Then pick a profile below for real work."
4. One-column section, no background. Heading "Pick a profile", a Text web part: "Start with the smallest profile that fits. Move up one when a job runs out of memory; a specialized profile is for the kind of job its row names.", then a List web part.
5. Two-thirds left section, no background. Left: heading "Common errors", then a List web part. Right: heading "Still stuck?", a Text web part: "Report it on Get help with the error and the cell that raised it. It becomes a ticket on our Jira board, and we triage it within {{team.triageDays}} business days.", and a Button web part "Report an issue" linking to Get-help.aspx.
6. One-column section, Neutral background. A Quick links web part, Compact layout: Kernel docs ({{kernel.docs.url}}), Source code ({{kernel.repo.url}}), Products (Products.aspx), Ask the Czars (Copilot.aspx).
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| title | Image layout | title area | background `assets/title-start.png`, topic header on |
| 1 | Two-thirds left, none | Text, Button | the button goes to section 2 on this page |
| 2 | One column, none | Text, List | `Access`, view `Checklist`; hide the command bar |
| 3 | Two-thirds left, Neutral | Text, Code snippet | Code snippet: language Python, dark theme, the cell under *Words* |
| 4 | One column, none | Text, List | `SparkProfiles`, view `Pick a profile`; hide the command bar |
| 5 | Two-thirds left, none | List, Text, Button | `FAQ`, view `Common errors`; hide the command bar |
| 6 | One column, Neutral | Quick links (Compact) | the source code link is for people with the Contributing code access |

## Words

Everything but the first session's cell is in the prompt: `{{kernel.summary}}`, `{{kernel.buildsOn}}`, the
packages, the sources, the setup steps and the kernel's name come from the data-czars scan, and the Confluence pages
fill what the repository does not say. The cell, exactly as the kernel's docs give it:

```python
{{kernel.firstSession}}
```

## Finish by hand

1. Title area: upload `assets/title-start.png`, focal point on the right, topic header on.
2. List web parts: list and view as the table says; **Hide command bar** on.
3. Section 3, right column: under the text, add a **Code snippet** web part (Copilot does not add one), language
   *Python*, theme *Dark*, and paste the cell above.
4. `Access`: open each row's *Where to request it* and check it lands on that entitlement's request.
5. Publish, and set the page description: "Get started with the {{kernel.name}}: access, setup, a first Spark session
   and the right profile."

## Check

- Someone with none of the access can follow the page from top to bottom without asking anyone.
- Someone with the access runs the cell in a new notebook, as written, and it works.
- Ask the site agent "What access do I need to use the kernel?" and "Which profile for a join of 50 million rows?":
  it answers from `Access` and `SparkProfiles` and cites them.
- The mega menu's Get started links land on their sections (`#what-you-get`, `#get-access`, `#set-up`,
  `#your-first-session`, `#pick-a-profile`, `#common-errors`).
