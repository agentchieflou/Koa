# Learn

**URL:** `SitePages/Learn.aspx`. **For:** everyone. **Design:** the canvas artboard *Learn*.

From a first install to writing skills, in three paths and one library. Every module and file is a row with a
level, a format, a tool and a review date, so the site agent can answer "where do I start?" and say which guide is
current.

## Build it with Copilot

From any page, open **Copilot** and ask it to create a page, then paste:

```text
Create a page called "Learn" for the Data Czars site. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

Title area: Image layout, topic header "Paths, guides and standards", title "Learn", and the description "From your first install to writing skills of your own, in three paths and one library."

1. Three-column section, no background, heading "Learning paths". In each column a List web part, titled "101: your first week", "201: running a fleet" and "301: building skills".
2. Two-thirds left section, no background. Left: heading "Guides and runbooks" and a Document library web part. Right: heading "Standards" and a Quick links web part, List layout, with these links and descriptions:
   - Data format policy: "Full data to disk, context gets TOON"
   - AGENTS.md conventions: "Thirty lines of facts, rules elsewhere"
   - Testing and the four held-out tiers: "What runs on every change, and why"
   - Refusals: "Versioned, named, never silent"
   - Pinned contracts: "Changed only by adopting a tag"
   - Contrast and accessibility: "Every colour measured, words carry status"
3. One-column section, Neutral background. Heading "Demos and recordings", then a Highlighted content web part, Card layout, three items.
4. One-column section, no background. Heading "Glossary", then a List web part.
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| title | Image layout | title area | background `assets/title-learn.png` |
| 1 | Three columns, none | List ×3 | `LearningPaths`, view `101`; `LearningPaths`, view `201`; `LearningPaths`, view `301` |
| 2 | Two-thirds left, none | Document library | `Guides`, view `Guides` |
| 2 | right column | Quick links, List | links below |
| 3 | One column, Neutral | Highlighted content | source: `Guides`, view `Recordings` (filter Kind = Recording), Card layout, 3 items |
| 4 | One column, none | List | `Glossary`, view `A to Z` |

The Standards links point at this-next-please: `docs/data-format-policy.md`, `AGENTS.md`, `docs/testing-this-repo.md`,
`docs/refusals.md`, Koa's `contract/PIN` and README §Contrast. When a standard is written for the whole bank rather
than for the repository, upload it to `Guides` with Kind = Standard and link that file instead.

## Words

All of it is in the prompt. The Guides rows the design shows (*Laptop setup and the XMLA sign-in*, *Windows
verification runbook*, *Building FleetAgent with a Copilot agent*, *Long Jira pulls without surprises*, *PBIP
authoring*, *Which shell runs which command*) are the first six files to put in `Guides`, exported from
this-next-please's `docs/setup.md`, `docs/windows-verification.md`, Koa's `build/README.md`, the README's Long Jira
pulls section, `docs/pbir-authoring.md` and `docs/shells.md`, each with Kind, Tool, Review by and Owner filled in.

## Finish by hand

1. Upload the six guides above to `Guides` and fill their columns; until then section 2 is empty.
2. Recordings: upload each demo video to `Guides` with Kind = Recording; Highlighted content picks them up.
3. Publish, and set the page description: "Learning paths, guides, standards and the glossary."

## Check

- Each path column shows its modules in step order, and a module with a link opens it.
- Ask the site agent "What does TOON mean?": it answers from the Glossary row.
