---
name: data-czars-pages
description: Builds and edits pages, sections and lists on the Data Czars site in the site's own style. Use whenever someone asks to create a page or news post, add or change a section, restyle a page, add a list or a column, or update rows that pages show (tools, releases, roadmap, decisions, metrics, FAQ, glossary).
---

# Data Czars pages

This site is the home of Data Czars, a tools and platform team. Pages here are built from stock web parts only, and
everything that changes often lives in a list, so a page never needs editing to stay true. Follow these rules for
every page, section, list and row you create or change on this site.

## Before you build

1. Say what you will build, section by section, naming each web part and the list and view it shows. Wait for a
   go-ahead before creating anything.
2. Check the lists below first. If what the person wants is already a list, show the list in a List web part; do not
   type its rows into a Text web part.

## Layout

- Sections: one column, two columns, three columns, one-third left, one-third right. No full-width sections (this is
  a team site) and no flexible sections.
- Backgrounds: None for any section holding a List, Document library or Quick chart web part (they keep the page
  background). Neutral or Soft for sections of text, quick links, people or calls to action. Strong only for the
  last section of the home page.
- Every page starts with a title area (Image layout for top-level pages, Plain for the rest), a topic header and a
  one-sentence description.
- Headings: one heading per section, in a Text web part, sentence case. Headings become the page's anchors, so keep
  their words when you move them.
- Use these web parts: Hero (Tiles), Quick links (Button, Compact, List or Grid), Text, List, Document library,
  Events, News, People, Call to action, Button, Code snippet, Image, Markdown, Highlighted content, Power BI report,
  Microsoft PowerApps, Agent Link. Ask before using anything else.

## Words

- Short sentences, plain words, active voice. Say what the reader can do, not what the team is proud of.
- Never invent a number, a date, a name or a promise. Where one is missing write a placeholder in square brackets:
  [N], [Date], [Name].
- A status is always a word ("Operational", "In progress", "Accepted"). Colour may help; it never carries the
  meaning alone.
- Commands and code go in a Code snippet web part, exactly as typed, never in running text.
- Name the tools as the Tools list names them: "ad-* CLI and skills", "The fleet", "FleetAgent", "Power BI toolkit",
  "Data connectors", "UAT reconciliation", "Document AI".

## Lists

| List | What it holds | Views to show on pages |
| --- | --- | --- |
| Tools | one row per tool: maturity, status, version, start command, docs | Catalog, Status, Featured |
| Releases | one row per release | Latest, All Items |
| Requests | work requested by partners | Mine (partners), Triage (members) |
| Roadmap | now, next, later | Now, Next, Later |
| Decisions | the decision log | Log |
| Glossary | the team's words, defined once | A to Z |
| FAQ | questions and answers, for partners or members | Partners, Members |
| Metrics | every number on the site, with its method | Tiles, Method |
| LearningPaths | the 101, 201 and 301 modules | 101, 201, 301 |
| WhoToAsk | who answers what | All Items |
| Onboarding | a new member's first month | All Items |
| Guides (library) | guides, runbooks, standards, recordings | Guides, Standards, Recordings |

When you add a row, fill every column the list asks for. A new release goes in Releases with Tool, Kind and the
notes; a new decision in Decisions with the next number, Status = Proposed, the context and the consequences. Never
delete a row: set a Retired, Superseded or Shipped value instead.

When you add a column to a list, give it an internal name with no spaces (rename the display name afterwards) and
tell the person which views and pages should show it.

## After you build

- Set the page description in Page details: one sentence on what the page is for.
- Give every image alt text.
- List what you could not do (formatting, permissions, a web part you could not configure) so a person can finish it.
