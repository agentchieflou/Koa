# Home

**URL:** `SitePages/Home.aspx`, the page the site already has: edit it, never create a second one.
**For:** everyone; members and partners see the same page. **Design:** the canvas artboard *Home*.

The front door. It answers four questions in the first screen (what is this, how do I start, can I get help, what
changed) and everything below it is live: status, releases, numbers, tools and roadmap come from lists, so the page
never needs editing to stay true.

## Build it with Copilot

Open the page, select **Edit**, then **Copilot**, and paste:

```text
Rebuild this page as the Data Czars home page. Remove what is on it now. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

1. One-column section, no background. A Hero web part, Tiles layout, five tiles:
   - Large tile: "Tools that make data work feel fast", call to action "Get started", linking to Platform.aspx.
   - "The fleet: every agent, one window", linking to The-fleet.aspx.
   - "Ship Power BI safely", linking to Platform.aspx.
   - "Bring us a data problem", linking to Work-with-us.aspx.
   - "What's new in 0.18", linking to Platform.aspx.
2. One-column section, Neutral background. Heading "Start here", then a Quick links web part, Button layout, with icons and descriptions:
   - Install the CLI: "The ad-* tools and the Copilot skills, together" (Platform.aspx)
   - Check your setup: "ad-doctor names every fix it finds" (Platform.aspx)
   - Open the fleet: "Every agent you run, in one window" (The-fleet.aspx)
   - Request work: "Reports, data pulls, automation, access" (Work-with-us.aspx)
   - Office hours: "Bring a data problem, leave with a plan" (Work-with-us.aspx)
   - Ask the Czars: "The site agent has read every page here" (opens the site agent)
3. Two-thirds left section, no background. Left: a List web part titled "Platform status". Right: an Events web part titled "Office hours and demos", Compact layout, three events.
4. Two-thirds left section, no background. Left: a News web part titled "What's new", Side-by-side layout. Right: a List web part titled "Releases".
5. One-column section, no background. A List web part titled "By the numbers".
6. Two-thirds left section, no background. Left: a List web part titled "Featured tools". Right: a List web part titled "On the roadmap now".
7. One-third left section, Soft background. Left: a Call to action web part with the text "Have a data problem? Bring it to office hours, or request work and we triage it within [N] business days." and the button "Request work" linking to Work-with-us.aspx. Right: a People web part titled "Meet the Czars", Descriptive layout.
8. One-third left section, Strong background. Left: a Text web part: "Data Czars · tools and platforms for the bank's data work". Right: a Quick links web part, Compact layout: Request work, Office hours, Status, Standards, Contact the team.
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| 1 | One column, no background | Hero, Tiles, 5 tiles | images `assets/hero-main.png`, `hero-fleet.png`, `hero-powerbi.png`, `hero-request.png`, `hero-release.png` |
| 2 | One column, Neutral | Quick links, Button layout | icons on, descriptions on; the last link opens the agent through an Agent Link web part if Copilot cannot link it |
| 3 | Two-thirds left, none | List | `Tools`, view `Status`; hide the command bar; size Small |
| 3 | right column | Events | the site's Events list, category Office hours and Demo, Compact, 3 events |
| 4 | Two-thirds left, none | News | this site, Side-by-side |
| 4 | right column | List | `Releases`, view `Latest`; hide the command bar |
| 5 | One column, none | List | `Metrics`, view `Tiles`; hide the command bar |
| 6 | Two-thirds left, none | List | `Tools`, view `Featured`; hide the command bar |
| 6 | right column | List | `Roadmap`, view `Now`; hide the command bar |
| 7 | One-third left, Soft | Call to action | background image `assets/cta.png` |
| 7 | right column | People | the team, Descriptive layout, each with their role |
| 8 | One-third left, Strong | Text, Quick links | Compact layout, five links |

List, Document library and Quick chart web parts always keep the page background, which is why every section that
holds one has none; the colour on this page comes from the hero, the formatted tiles and sections 2, 7 and 8.

## Words

Everything Copilot needs is in the prompt. The sentences that carry a promise: "we triage within [N] business days"
(sections 7 and the FAQ) must name the same number, and that number is the team's to set before the page is published.

## Finish by hand

1. Hero: upload the five images from `site/assets/` (Change image > Upload), set each tile's link if Copilot left it
   empty, and write alt text: the tile's own title.
2. Each List web part: **Edit web part** > list and view as the table says; turn **Hide command bar** on; title as the
   prompt says. The formatted views come from the provisioning step, so the tiles, pills and rows appear by themselves.
3. Events: add the three office hours and demo events to the Events list first, each with Category set.
4. People: add each member with their role as the description.
5. Section 8 replaces a footer, which team sites do not have.
6. Publish. Then **Page details** > *Description*: "Data Czars: tools and platforms for the bank's data work." The
   agent and search both read it.

## Check

- At 1280 px and on a phone: nothing clipped, the hero stacks, every list web part shows its formatted rows.
- Every status reads as a word, never as colour alone.
- Ask the site agent "What is on the roadmap now?": its answer cites the Roadmap list.
- The accessibility of the page: every image has alt text, headings go in order (one H1, then H2s).
