# Platform

**URL:** `SitePages/Platform.aspx`. **For:** everyone. **Design:** the canvas artboard *Platform*.

Every tool we build and support, what state it is in, and how to start with it in under ten minutes. The catalog,
the status and the releases are lists; the page itself only changes when the install commands do.

## Build it with Copilot

From any page, open **Copilot** and ask it to create a page, then paste:

```text
Create a page called "Platform" for the Data Czars site. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

Title area: Image layout, topic header "The Data Czars platform", title "Platform", and the description "Every tool we build and support, what state it is in, and how to start with it in under ten minutes."

1. One-column section, no background. A Quick links web part, Compact layout, with seven links: All, Agent platform, Data and BI, Testing and UAT, Document AI, Developer experience, Mobile.
2. One-column section, no background. Heading "Tool catalog", then a List web part.
3. Two-column section, Neutral background.
   Left: heading "Get started in four commands", the text "Once per laptop, never inside a project repository. The CLI needs Python 3.14 or newer.", then a Code snippet web part, language PowerShell, with these four lines:
   gh skill install agentchieflou/this-next-please --all --scope user
   pip install "agentdata @ git+https://github.com/agentchieflou/this-next-please.git"
   ad-setup
   ad-doctor
   Right: heading "Keep it current", the text "The CLI and the skills move together. Update both, then start a new Copilot chat so it reads the new skills.", then a Code snippet web part, language PowerShell, with these three lines:
   ad-update            # reinstall the CLI and every skill, say what changed
   ad-update --check    # what you are running right now
   ad-setup --patch     # after any fail row in ad-doctor
4. Two-thirds left section, no background. Left: heading "Releases" and a List web part. Right: heading "Status", a List web part, and a Button web part "Report a problem" linking to Work-with-us.aspx.
5. One-column section, Soft background. Heading "Skills library", the text "51 Copilot skills, one job each. The router picks exactly one for every request.", then a Markdown web part.
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| title | Image layout | title area | background `assets/title-platform.png`, topic header on |
| 1 | One column, none | Quick links, Compact | each link opens the Tools list filtered to one category: `Lists/Tools/Catalog.aspx?FilterField1=Category&FilterValue1=<category>` |
| 2 | One column, none | List | `Tools`, view `Catalog`; command bar on, so people can search |
| 3 | Two columns, Neutral | Text, Code snippet ×2 | language PowerShell, theme Dark |
| 4 | Two-thirds left, none | List | `Releases`, view `All Items` |
| 4 | right column | List, Button | `Tools`, view `Status`, size Small; Button to Work-with-us.aspx |
| 5 | One column, Soft | Markdown | the table below |

## Words

The Markdown web part in section 5 holds the skills table. Regenerate it from this-next-please's `skills/` folder when
a skill is added or removed, and change the count in the sentence above it to match:

```markdown
| Family | Skills |
| --- | --- |
| Routing and sessions | router · code-router · data-router · session-bootstrap · state-update · run-control |
| Power BI | pbi-router · pbi-report-plan · pbi-report-design · pbi-report-author · pbi-validate · pbi-publish · pbi-deploy-te2 · pbi-refresh-xmla · pbi-verify-service · pbi-model-audit · pbi-observe · pbi-custom-visual · tmdl-edit · pbip-projection · dax-studio-export |
| Data | data-adapter · teradata-query · oracle-query · hive-query · slurm-submit · perf-optimize |
| Jira, Bitbucket, Confluence | jira-router · jira-create · jira-triage · jira-transition · jira-comment · jira-changelog · bitbucket-pr · confluence-publish |
| Testing and UAT | test-cover · test-regress · uat-jira-vs-source · uat-jira-vs-warehouses · uat-report-visual |
| Documents and code | dpm-router · dpm-field-extraction · dpm-consumer-integration · content-understanding-extract · codebase-map · project-onboard · code-change · research-spike · file-organize · friction-log · worktree-tidy |
```

## Finish by hand

1. Title area: upload `assets/title-platform.png`, focal point on the right, topic header on.
2. Quick links in section 1: set each link to the filtered view URL the table gives; the first, *All*, to
   `Lists/Tools/Catalog.aspx`.
3. List web parts: list and view as the table says. The Catalog view is a gallery whose cards come from
   `formatting/tools-catalog.json`.
4. Headings in Text web parts become the page's anchors (`#tool-catalog`, `#releases`, `#status`, `#skills-library`,
   `#get-started-in-four-commands`), which the mega menu links to. Keep the words exactly, or update `site/site.json`.
5. Publish, and set the page description: "Every Data Czars tool, its state, and how to start."

## Check

- The mega menu's Platform links each land on their section.
- A filter link shows only that category's cards.
- The code snippets copy cleanly (no smart quotes): paste one into a terminal.
