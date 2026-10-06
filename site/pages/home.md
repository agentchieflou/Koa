# Home

**URL:** `SitePages/Home.aspx`, the page the site already has: edit it, never create a second one.
**For:** everyone who uses the PAE and the team. **Design:** the canvas artboard *Home*.

The front door. In the first screen it answers what Data Czars is, how to start with the kernel, how to get help,
where the usage reports are and who to talk to. Everything below it is live: product status, the latest reports, releases and featured products come
from lists and the library, so the page never needs editing to stay true.

## Build it with Copilot

`python site/provision.py pages` fills in the double-braced facts from the scans and writes this prompt, ready
to paste, to `site/out/pages/home.md`. Open the page, select **Edit**, then **Copilot**, and paste:

```text
Rebuild this page as the Data Czars home page. Remove what is on it now. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

1. One-column section, no background. A Hero web part, Tiles layout, five tiles:
   - Large tile: "Data Czars: tooling for the PAE", call to action "Get started", linking to Get-started.aspx.
   - "Report an issue", linking to Get-help.aspx.
   - "Usage reports", linking to Usage-reports.aspx.
   - "Talk to the team", linking to Contact.aspx.
   - "Data Czars in Copilot", linking to Copilot.aspx.
2. One-column section, Neutral background. A Text web part with "{{team.mission}} {{team.audience}}", then heading "Start here" and a Quick links web part, Button layout, with icons and descriptions:
   - Get started: "Access, setup and your first Spark session" (Get-started.aspx)
   - Report an issue: "Something broken in a product we support" (Get-help.aspx)
   - Request something: "A change, a new feature, a question or access" (Get-help.aspx)
   - My tickets: "Where your requests stand in Jira" (Get-help.aspx#my-tickets)
   - Usage reports: "This period's reports, ready to download" (Usage-reports.aspx)
   - Contact the team: "The right person, the way they like to be reached" (Contact.aspx)
3. Two-thirds left section, no background. Left: heading "Product status" and a List web part. Right: heading "Latest usage reports" and a Document library web part.
4. Two-thirds left section, no background. Left: a News web part titled "News", Side-by-side layout. Right: heading "What's new" and a List web part.
5. One-column section, no background. Heading "Featured products", then a List web part.
6. One-third left section, Soft background. Left: a Call to action web part with the text "Something not working? Report it here: it becomes a ticket on our Jira board, and we triage it within {{team.triageDays}} business days." and the button "Report an issue" linking to Get-help.aspx. Right: heading "Ask the Czars" and an Agent Link web part.
7. One-third left section, Strong background. Left: a Text web part: "Data Czars · tooling for the PAE". Right: a Quick links web part, Compact layout: Links (Links.aspx), Jira board ({{jira.boardUrl}}), Contact (Contact.aspx), Get help (Get-help.aspx).
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| 1 | One column, no background | Hero, Tiles, 5 tiles | images `assets/hero-main.png`, `hero-help.png`, `hero-reports.png`, `hero-contact.png`, `hero-copilot.png` |
| 2 | One column, Neutral | Text, Quick links (Button) | icons on, descriptions on |
| 3 | Two-thirds left, none | List | `Products`, view `Status`; hide the command bar |
| 3 | right column | Document library | `UsageReports`, view `Latest`; hide the command bar |
| 4 | Two-thirds left, none | News | this site, Side-by-side |
| 4 | right column | List | `Releases`, view `Latest`; hide the command bar |
| 5 | One column, none | List | `Products`, view `Featured`; hide the command bar |
| 6 | One-third left, Soft | Call to action, Agent Link | CTA background `assets/cta.png`; Agent Link: *Ask the Czars* (`agents/ask-the-czars.md`) |
| 7 | One-third left, Strong | Text, Quick links (Compact) | stands in for the footer team sites do not have |

List, Document library and Quick chart web parts always keep the page background, which is why every section that
holds one has none; the colour on this page comes from the hero, the formatted tiles and sections 2, 6 and 7.

## Words

Everything is in the prompt. `{{team.mission}}` and `{{team.audience}}` come from the data-czars scan; the triage
promise, `{{team.triageDays}}` business days, is the team's to set in `site/local/context.json`, and must read the
same here, on Get help and in the FAQ.

## Finish by hand

1. Hero: upload the five images from `site/assets/` and give each its tile's title as alt text.
2. Each List and Document library web part: list and view as the table says; **Hide command bar** on. The formatting
   comes from the provisioning, so the status tiles, cards and rows appear by themselves.
3. Agent Link: pick *Ask the Czars* once it exists (`site/agents/ask-the-czars.md`).
4. Publish. Then **Page details** > *Description*: "Data Czars: tooling for the PAE, help, usage reports and the
   team." Search and the agents both read it.

## Check

- At 1280 px and on a phone: nothing clipped, the hero stacks, every list shows its formatted rows.
- Every status reads as a word, never as colour alone.
- Ask the site agent "Which products are not Operational right now?": it answers from the Products list and cites it.
