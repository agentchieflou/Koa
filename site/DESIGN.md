# The Data Czars site: the design

`OSP-Data-Czars` is the SharePoint home of Data Czars and of the tooling it supports in the PAE: the shared kernel and
the Spark tooling built in the `data-czars` repository. It is where people get access and start their first Spark
session, find a product and its state, raise an issue with it or ask for work (and follow it in Jira without opening
Jira), download the usage reports the `usage_tool` repository produces, find every place the team works, and reach the
right person the way that person prefers. The fleet that works the team's tickets has one page of its own. Copilot can
do all of it from a chat. `README.md` beside this file is the build sheet; the canvas *Data Czars Site Design* shows
every page as drawn.

A premier site, for a tools and platform team, behaves like a product: a person gets what they came for in one
click, every fact on it is current without anyone remembering to edit a page, it answers and acts from Copilot, and
the team's own systems (Jira, the fleet, the usage tool) feed it instead of people retyping into it.

## Who it is for

| Audience | Who | What they come to do | Where it starts |
| --- | --- | --- | --- |
| Users of the PAE | people who use the kernel and tooling Data Czars supports (the site's Visitors) | get access and set up; start Spark with the right profile; fix a common error; check a product's state; report an issue; ask for work; follow their tickets; read the usage reports; reach someone | Home, Get started, Get help, Usage reports, Contact |
| The team | the Data Czars (the Microsoft 365 group) | triage intake; publish reports; keep products, links and contacts current; run the fleet | Get help (For the team), The fleet, the lists |
| Leaders | sponsors and their staff | see what is supported, what changed, and what usage looks like | Products, Usage reports |

## Principles

1. **Task first.** Home answers what this is, how to start, how to get help, where the reports are and who to talk
   to, above the fold. Every page opens with one sentence saying what it is for.
2. **Fed, not typed.** Products, profiles, releases and links come from scanning the repositories; access and setup
   from the team's Confluence pages; contacts from Microsoft Copilot; Jira keys and statuses from Jira; reports from
   the usage tool. People edit a row only to correct it.
3. **One door for help.** Issues, requests, questions and access the team grants go through one form and one list,
   and every one becomes a Jira ticket whose status comes back. Nobody is told "email us". Entitlements the
   organisation grants are requested where their `Access` row links, never through the team.
4. **People, their way.** Every team member chooses how to be reached; the site honours it with one button.
5. **Copilot-native.** The site's structure, descriptions and metadata are what its agents read. Three agents divide
   the work: answers (Ask the Czars), numbers (Usage Analyst), actions (Czars Desk).
6. **Stock parts, no admin.** Stock web parts in stock sections on a team site; Standard connectors; nothing a site
   owner cannot do. What an admin could add is listed, not assumed.
7. **The structure is public, the facts are not.** Koa is public, so it carries the design, the code and the prompts;
   what the scans find about the team stays on the laptop (`site/local/`) and reaches only the site.

## Information architecture

Horizontal navigation with a mega menu, the exact tree in `site.json`:

| Label | Links |
| --- | --- |
| Home | |
| Get started | What you get, Get access, Set up, Your first session, Pick a profile, Common errors |
| Products | Product catalog, Status, What's new |
| Usage reports | Latest reports, All reports, About the usage tool |
| Get help | Report an issue, Request something, My tickets, FAQ · **For the team** (targeted): Triage, Jira board |
| Links | |
| Contact | |
| The fleet | |
| Copilot | Ask the Czars, Prompts that work, In Teams |

Nine pages, nine lists and one library:

| Page | Holds | Lists and views it shows |
| --- | --- | --- |
| Home | the front door | Products: Status, Featured · UsageReports: Latest · Releases: Latest |
| Get started | access, setup, a first Spark session, which profile, common errors | Access: Checklist · SparkProfiles: Pick a profile · FAQ: Common errors |
| Products | the catalog, what changed, status | Products: Catalog, Status · Releases: All Items |
| Usage reports | the reports and how the tool works | UsageReports: Latest, By report |
| Get help | the form, what happens next, my tickets, FAQ | Intake: Mine · FAQ: Everyone |
| Links | every place the team works | Links: By category |
| Contact | the team, each with their preferred way | Contacts: Cards |
| The fleet | the agents that work the tickets; FleetAgent embedded | FleetAgent (Power Apps), shared with the fleet session |
| Copilot | the agents, prompts, Teams and schedules | Prompts: Library |

What goes where:

| It is | It goes in | Fed by |
| --- | --- | --- |
| the kernel, or a capability a person calls by name, and its state | a `Products` row | the data-czars scan; the owner edits the status |
| an entitlement the kernel needs | an `Access` row | the Confluence pages, then the data-czars scan |
| a Spark resource profile | a `SparkProfiles` row | the data-czars scan of the session code |
| how to set up, the first session | the Get started page | the data-czars scan and the Confluence pages |
| a release | a `Releases` row | the scans (changelog, tags) |
| an issue, a request, a question, access | an `Intake` row, then a Jira ticket | the Get help form or Czars Desk; the key and status from Jira |
| a usage report | a file in `UsageReports/<type>/<yyyy-mm>/` | the usage tool; tagged by its folder |
| a place the team works | a `Links` row | the scans and Microsoft Copilot |
| a person and how to reach them | a `Contacts` row | Microsoft Copilot; each person sets their preference |
| a question asked twice, a common error and its fix | an `FAQ` row | the scans and the Confluence pages; the team |
| a prompt that works | a `Prompts` row | the team |
| an announcement | a news post | the team |

## Help, end to end

Get help's form writes an `Intake` row. A Standard flow hands it to the operator's laptop as a file; `intake.py`
files it with `ad-jira create`, which uses the project's facts and waits for one approval on the desk or the phone;
a second flow writes the key, the link and the status back to the row. `intake.py sync` keeps the status following
Jira. The ticket lands on the same board the fleet works from, so a reported issue can reach an agent working on
data-czars, and its fix reach the person who reported it, without anyone copying anything. Why through the laptop,
and the routes that avoid it when IT allows: `intake/README.md`.

## Copilot

- **Ask the Czars**: the site agent in the header, in Microsoft Copilot and in Teams; answers from the site's pages,
  lists and reports, with citations, and never guesses.
- **Usage Analyst**: an Agent Builder agent whose knowledge is the report files; code interpreter computes the answer
  and draws the chart.
- **Czars Desk**: a Copilot Studio agent whose tools act as the person asking: file a request, list their requests,
  get the latest report, open the right person's preferred contact.
- **Copilot in SharePoint** builds the pages from their sheets and keeps the house style through the site skill
  `data-czars-pages`.
- Teams tabs and posts, scheduled prompts, the Prompt Gallery, and one request to IT for the Jira and Confluence
  connectors: `agents/README.md`.

## Pages

Every page follows one anatomy, which the site skill enforces: a title area (Image layout, a topic header, one
sentence); one-, two- or three-column sections, or one-third left or right, never full-width (communication sites
only) or flexible; no background behind a List or Document library web part (they keep the page background), Neutral
or Soft behind text and calls to action, Strong once, for Home's last section, which stands in for the footer team
sites lack; one heading per section, which becomes the anchor the mega menu links to.

## Visual system

- **Theme: Teal**, a built-in theme: modern, technical, distinct from the bank's blue sites; white text on its
  primary (`#03787C`) is 5.3:1. An organisation brand theme from Brand center wins if there is one, and
  `assets/make_assets.py --accent` redraws the artwork in it.
- **Header**: Standard layout, no background, the mark as logo, the title "Data Czars", the Copilot button opening
  Ask the Czars.
- **The mark**: three bars that are also a crown, on a rounded square in the theme colour (`assets/logo.svg`).
- **Artwork**: flat geometry in shades of the theme colour, no text, no stock photos, one motif per subject.
- **Lists**: formatted, never raw. Statuses are pills with an icon and a word; products and contacts are cards; a
  contact card's button follows the person's preference; links group by place with an icon; reports have a Download
  link. All formatting uses SharePoint's theme classes, so it follows a theme change.
- **Type**: SharePoint's own. Sizes come from the web parts.

## Voice

Short sentences, plain words, active voice; say what the reader can do. Products are named as the Products list names
them. Never invent a number, a date, a name or a promise. The triage promise, the team's own number of business days,
reads the same everywhere it appears.

## Permissions

| Who | Gets | How |
| --- | --- | --- |
| The team | edit everywhere | the Microsoft 365 group |
| Users of the PAE | read the site; submit and see their own requests; download reports | the site's Visitors group; `Intake` has item-level read and edit, and Visitors get Contribute on it alone |
| The team only, visible | Get help's *For the team* links and menu group | audience targeting to the Members group |
| The team only | FleetAgent's lists | their own permissions |

## Keeping it premier

- The scans run again when the repositories change; `provision.py context` and step 2 bring the new rows in.
- *Improve this site* in Copilot runs monthly: demote pages inactive for 90 days and fix broken links.
- Page analytics and site usage are read monthly; a page nobody opens is merged or demoted.
- A change to the site starts in Koa: the spec or the sheet, the tests, a pull request, then the site.

## Not in this design

- No site footer, full-width section or communication-site feature: this is a team site.
- No custom code, app or extension, and no Premium connector.
- No copy of the FleetAgent lists, flows or app: Koa's `build/` and the fleet session own them.
