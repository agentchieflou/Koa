# Usage reports

**URL:** `SitePages/Usage-reports.aspx`. **For:** everyone with access to the site.
**Design:** the canvas artboard *Usage reports*.

Where the usage tool's reports land, for the site's members to read and download, with what the tool is and how it
works. The reports live in the `UsageReports` library; each lands in a folder named for its report type and month,
and the `CzarsTagReports` flow tags it from that folder (`site/intake/README.md` §Usage reports).

## Build it with Copilot

From any page, open **Copilot** and ask it to create a page, then paste (`site/out/pages/usage-reports.md` has it filled in):

```text
Create a page called "Usage reports" for the Data Czars site. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

Title area: Image layout, topic header "{{usageTool.name}}", title "Usage reports", and the description "{{usageTool.summary}}"

1. One-column section, no background. Heading "Latest reports", then a Document library web part.
2. Two-thirds left section, Neutral background.
   Left: heading "About the usage tool", then a Text web part with three short paragraphs:
   - "How it works: {{usageTool.howItWorks}}"
   - "When: {{usageTool.schedule}}"
   - "Reports: {{usageTool.reportTypes[].name}}."
   Right: heading "A question about a report?", the text "Ask the person who owns the reports, or raise it on Get help.", and two Button web parts: "Contact the team" linking to Contact.aspx, and "Get help" linking to Get-help.aspx.
3. One-column section, no background. Heading "All reports", then a Document library web part.
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| title | Image layout | title area | background `assets/title-reports.png` |
| 1 | One column, none | Document library | `UsageReports`, view `Latest`; command bar off |
| 2 | Two-thirds left, Neutral | Text, Button ×2 | |
| 3 | One column, none | Document library | `UsageReports`, view `By report`; command bar on |

## Words

All of it is in the prompt; every fact comes from the usage_tool scan. If the tool's schedule or its report types
change, run the scan again, `python site/provision.py context`, then ask Copilot on this page to update section 2.

## Finish by hand

1. Library: in `UsageReports`, create one folder per report type (`{{usageTool.reportTypes[].name}}`), each with a
   folder per month as reports arrive (`2026-10`). Library settings > **Column default value settings**: set each
   type folder's **Report** default to its own type, so even a file dragged in by hand is tagged.
2. Permissions: the library inherits the site's, so everyone who can open the site can read and download a report.
   To narrow it, stop inheriting on the library and grant Read to the groups who may see usage.
3. Publish, and set the page description: "The usage tool's reports, ready to download, and how the tool works."

## Check

- A report copied into `UsageReports/<report type>/<yyyy-mm>/` shows in *Latest reports* within the hour, tagged
  with its type and period, and its *Download* link downloads it.
- Ask the site agent "Where is last month's usage report?": it links the file.
