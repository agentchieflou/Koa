# The Data Czars site: the design

`OSP-Data-Czars` on SharePoint is the home of Data Czars, a tools and platform team: the tools and platforms we build
for the bank's data work, how to start with them, how to work with us, what changed, and who we are. This page is the
design and the reasons for it. `README.md` beside it is the build sheet; the canvas *Data Czars Site Design* shows
every page as drawn (ask the operator for the link).

A premier site, for a tools and platform team, is one that behaves like a product: a person finds what they came for
in one click, every fact on it is current without anyone remembering to edit a page, it answers questions itself,
and it can show what it is worth. Everything below serves one of those four.

## Who it is for

| Audience | Who | What they come to do | Where it starts |
| --- | --- | --- | --- |
| Partners | data teams across the bank (the site's Visitors) | find a tool and start with it; ask for help; request work and follow it | Home, Platform, Work with us |
| Members | the Data Czars (the Microsoft 365 group) | everything partners do, plus decide, onboard, run the fleet | Team, The fleet, Onboarding |
| Leadership | sponsors and their staff | see what the platform gives back and what comes next | Impact, Roadmap |

The site is the group's team site, so members are the group and everyone else is added to its Visitors group. What
only members should see is limited by permissions (a page, a list) or by audience targeting (navigation links, quick
links, news, events), never by hoping nobody finds a URL.

## Principles

1. **Task first.** Home answers four questions above the fold: what is this, how do I start, how do I get help, what
   changed. Every page opens with a title area and one sentence saying what it is for.
2. **Living data, typed once.** Anything that changes (tools, status, releases, roadmap, decisions, numbers,
   questions, words) is a list row, shown by a formatted list view. A page changes when its purpose does, not when a
   fact does.
3. **Built for Copilot.** Clean structure, descriptive titles, a description on every page, metadata on every file,
   review dates on every guide: the same things that make search work make the site agent's answers good. The site
   carries its own Copilot skill so everything Copilot builds here keeps the house style.
4. **Measured, not claimed.** No number appears without a row saying how it is counted and where it comes from.
   Until the team agrees a method, the number is a placeholder and says so.
5. **Accessible as drawn.** Every status is a word; colour only helps. Every image has alt text. Headings go in order.
   Text meets 4.5:1 against what it sits on.
6. **Stock parts, no admin.** Every page is stock web parts in stock sections on a team site. No SharePoint Framework,
   no custom script, nothing a site owner cannot do. That keeps it supportable and lets Copilot build it.
7. **The site is code.** Its lists, views, formatting, page sheets, navigation, skill and agent live in Koa, are
   reviewed in pull requests and tested in CI. The live site is built from the repository, and a change starts here.

## Information architecture

Navigation is horizontal with a mega menu: six labels, two levels beneath each, the exact tree in `site.json`.

| Label | Groups and links |
| --- | --- |
| Home | |
| Platform | **Tools**: Tool catalog, Getting started, Status, What's new · **Agent platform**: The fleet, FleetAgent on your phone, Skills library, The world (lab) · **Data and BI**: Power BI toolkit, Data connectors, UAT reconciliation, Document AI |
| Work with us | **Engage**: Services, Request work, My requests · **Plan**: Roadmap, Office hours, FAQ |
| Learn | **Paths**: 101, 201, 301 · **Library**: Guides and runbooks, Standards, Demos and recordings, Glossary |
| Team | **About**: Mission and principles, People, Who to ask · **Members** (targeted): Onboarding, Decisions, Team calendar, Notebook |
| Impact | |

Eight pages, twelve lists and one library:

| Page | Holds | Lists and views it shows |
| --- | --- | --- |
| Home | the front door | Tools: Status, Featured · Releases: Latest · Metrics: Tiles · Roadmap: Now |
| Platform | the catalog, install, releases, status, skills | Tools: Catalog, Status · Releases: All Items |
| The fleet | the daily loop, FleetAgent embedded, the four views | FleetAgent (Power Apps), shared with the fleet session |
| Work with us | engage, request, follow, roadmap, FAQ | Requests: Mine · Roadmap: Now, Next, Later · FAQ: Partners |
| Learn | paths, guides, standards, recordings, glossary | LearningPaths: 101, 201, 301 · Guides · Glossary: A to Z |
| Team | principles, people, who to ask, decisions | WhoToAsk · Decisions: Log |
| Impact | adoption, method, stories | Power BI report · Metrics: Tiles, Method |
| Onboarding | first day, week, month (members only) | Onboarding · LearningPaths: 101 · FAQ: Members |

What goes where:

| It is | It goes in | Because |
| --- | --- | --- |
| a fact that changes (a status, a version, an owner, a date) | a list row | one edit updates every page that shows it, and the agent can cite the row |
| an announcement | a news post | news rolls up to Home, the news digest and the SharePoint app |
| a document (guide, runbook, standard, deck, recording) | the Guides library, with Kind, Tool, Review by, Owner | metadata tells a current runbook from an old one |
| an explanation that rarely changes | a page | pages are for purpose and narrative |
| a decision | a Decisions row | numbered, never deleted, superseded rows stay |
| a question asked twice | an FAQ row | partners see their rows; the agent answers from them |

## Pages

Every page follows one anatomy, which the site skill enforces:

- **Title area**: Image layout with the page's artwork for top-level pages, Plain for the rest; a topic header; one
  sentence on what the page is for.
- **Sections**: one, two or three columns, or one-third left or right. No full-width sections (communication sites
  only) and no flexible sections, so every page reflows the same way on a phone.
- **Backgrounds**: none behind any List, Document library or Quick chart web part, because those always keep the page
  background and would sit as white boxes on a coloured band. Neutral and Soft carry text, quick links, people and
  calls to action; Strong is used once, for Home's last section, which stands in for the footer team sites lack.
- **Headings**: one per section, sentence case, in a Text web part. They become anchors the mega menu links to.
- **Web parts**: Hero (Tiles), Quick links, Text, List, Document library, Events, News, People, Call to action,
  Button, Code snippet, Image, Markdown, Highlighted content, Power BI report, Microsoft PowerApps, Agent Link.

Each page has a sheet in `pages/`: its Copilot prompt, every section and web part with its list and view, the words,
what to finish by hand, and how to check it.

## Visual system

- **Theme: Teal**, one of SharePoint's built-in themes. It reads as modern and technical, stands apart from the
  bank's corporate blue sites, and white text on its primary (`#03787C`) is 5.3:1. If the organisation publishes a
  brand theme in Brand center, that wins; Green (today's theme), Blue and Cobalt are the built-in alternatives, and
  `assets/make_assets.py --accent` redraws the artwork in any of them.
- **Header**: Standard layout, no background, the mark as the site logo, the title "Data Czars". The header's Copilot
  button opens the site agent.
- **The mark**: three bars that are also a crown, on a rounded square in the theme colour (`assets/logo.svg`). It is
  the site's logo and thumbnail.
- **Artwork**: flat geometry in four shades of the theme colour (deep, mid, light, line), no text, no stock photos, no
  gradients. One motif per subject: a network and bars (the platform), a desk of tiles (the fleet), rising bars and a
  check (Power BI), a path to an arrow (requests), a spark (what is new), a rising line (impact).
- **Lists**: formatted, never raw. Statuses are pills with an icon and a word (`formatting/*-status.json`), the catalog
  and featured tools are cards, the numbers are tiles in the theme colour, releases, roadmap, decisions, FAQ, glossary
  and learning paths are formatted rows. All formatting uses SharePoint's theme classes, so it follows a theme change.
- **Type**: SharePoint's own (Segoe UI). Sizes come from the web parts; the design adds none.

## Voice

Short sentences, plain words, active voice. Say what the reader can do. Name tools as the Tools list names them.
Commands go in Code snippet web parts exactly as typed. Never invent a number, date, name or promise: write [N],
[Date], [Name] until the real one exists. The one promise the site makes in several places, "we triage within [N]
business days", must read the same number everywhere it appears.

## Copilot and the site agent

- **Copilot in SharePoint** builds the pages from their sheets (`pages/*.md`), the navigation from its prompt, and
  any list the provisioning cannot. It does not reliably apply list formatting and does not set permissions, so
  those stay in the provisioning and the sheets' *Finish by hand*.
- **The site skill** `data-czars-pages` (`skills/data-czars-pages/SKILL.md`) lives in the site's Agent Assets library
  and loads whenever someone asks Copilot to build or edit on this site: layout rules, web part vocabulary, the lists,
  the voice.
- **Ask the Czars** (`agent/ask-the-czars.md`) is the site agent the header opens: grounded in this site only, citing
  every answer, never guessing a number, never touching requests.

## Permissions

| Who | Gets | How |
| --- | --- | --- |
| Members | edit everywhere | the Microsoft 365 group |
| Partners | read the site; add and see only their own requests | the site's Visitors group; Requests has item-level read and edit, and Visitors get Contribute on it alone |
| Members only | Onboarding; the FleetAgent lists | page and list permissions, Visitors removed |
| Members only, visible | the Members links in Team and the mega menu | audience targeting to the Members group |

## Keeping it premier

- Every page and guide has an owner and a review date. *Improve this site* in Copilot runs monthly: demote pages
  inactive for 90 days and fix broken links.
- Page analytics and site usage are read once a month; a page nobody opens is merged or demoted.
- A change starts in Koa: edit the spec or the sheet, run the tests, open a pull request, then apply it to the site.

## Not in this design

- No site footer, full-width section or communication-site feature: this is a team site, and converting it is
  neither possible (group-connected) nor needed.
- No custom code, apps or extensions: everything is stock and a site owner can do it.
- No copy of the FleetAgent lists, flows or app: Koa's `build/` and the fleet session own those; the fleet page only
  shows them.
