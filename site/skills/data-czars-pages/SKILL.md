---
name: data-czars-pages
description: Builds and edits pages, sections and lists on the Data Czars site in the site's own style. Use whenever someone asks to create a page or news post, add or change a section, restyle a page, add a list or a column, or update rows that pages show (products, releases, links, contacts, FAQ, prompts, usage reports).
---

# Data Czars pages

This site is the home of Data Czars, the team that supports tooling in the PAE. Pages here are built from stock web
parts only, and everything that changes lives in a list or a library, so a page never needs editing to stay true.
Follow these rules for every page, section, list and row you create or change on this site.

## Before you build

1. Say what you will build, section by section, naming each web part and the list and view it shows. Wait for a
   go-ahead before creating anything.
2. Check the lists below first. If what the person wants is already a list, show the list in a List web part; never
   type its rows into a Text web part.

## Layout

- Sections: one column, two columns, three columns, one-third left, one-third right. No full-width sections (this is
  a team site) and no flexible sections.
- Backgrounds: None for any section holding a List, Document library or Quick chart web part (they keep the page
  background). Neutral or Soft for sections of text, quick links, buttons or calls to action. Strong only for the
  last section of the home page.
- Every page starts with a title area (Image layout), a topic header and a one-sentence description.
- Headings: one heading per section, in a Text web part, sentence case. Headings become the page's anchors, so keep
  their words when you move them.
- Use these web parts: Hero (Tiles), Quick links (Button, Compact, List or Grid), Text, List, Document library, News,
  Button, Call to action, Image, Agent Link, Microsoft PowerApps. Ask before using anything else.

## Words

- Short sentences, plain words, active voice. Say what the reader can do, not what the team is proud of.
- Never invent a number, a date, a name or a promise. Where one is missing write a placeholder in square brackets:
  [N], [Date], [Name].
- A status is always a word ("Operational", "In progress", "Done"). Colour may help; it never carries the meaning
  alone.
- Commands go in a Code snippet web part, exactly as typed, never in running text.
- Name products as the Products list names them. Point every "how do I get help" to the Get help page; never to an
  email address.

## Lists

| List | What it holds | Views to show on pages |
| --- | --- | --- |
| Products | one row per supported product: support level, status, version, how to start, docs | Catalog, Status, Featured |
| Releases | one row per release of a product | Latest, All Items |
| Intake | issues, requests, questions and access; each becomes a Jira ticket | Mine (everyone), Triage, Open (the team) |
| Links | every place the team works, by category | By category |
| Contacts | the team, what to ask each about, and their preferred way to be reached | Cards |
| FAQ | questions and answers | Everyone |
| Prompts | prompts that work in Microsoft Copilot and the team's agents | Library |
| UsageReports (library) | the usage tool's reports, by type and period | Latest, By report |

When you add a row, fill every column the list asks for. Never delete a row: set Retired, Deprecated, Superseded or
Declined instead. Never change an Intake row's Jira, Jira link, Status or Last sync: the Jira flows own them.

When you add a column, give it an internal name with no spaces (rename the display name afterwards) and tell the
person which views and pages should show it.

## After you build

- Set the page description in Page details: one sentence on what the page is for.
- Give every image alt text.
- List what you could not do (formatting, permissions, a web part you could not configure) so a person can finish it.
