# Impact

**URL:** `SitePages/Impact.aspx`. **For:** everyone, leadership first. **Design:** the canvas artboard *Impact*.

What the platform gives back, measured, not claimed. No number appears on this page until its row in `Metrics` says
how it is counted and where it comes from.

## Build it with Copilot

From any page, open **Copilot** and ask it to create a page, then paste:

```text
Create a page called "Impact" for the Data Czars site. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

Title area: Image layout, topic header "Measured, not claimed", title "Impact", and the description "What the platform gives back to the bank, counted the same way every week, with the method written down beside every number."

1. One-column section, no background. Heading "Platform adoption", then a Power BI report web part.
2. One-column section, no background. A List web part titled "By the numbers".
3. One-column section, Neutral background. Heading "How we count", then a List web part.
4. One-column section, no background. Heading "Stories", then a News web part, Tiles layout.
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| title | Image layout | title area | background `assets/title-impact.png` |
| 1 | One column, none | Power BI report | the *Platform adoption* report, page Overview; navigation pane and action bar off |
| 2 | One column, none | List | `Metrics`, view `Tiles`; command bar off |
| 3 | One column, Neutral | List | `Metrics`, view `Method` |
| 4 | One column, none | News | this site, Tiles layout, filtered to news posts whose page property `Story` is Yes |

## Words

All of it is in the prompt. A story's title names the team and the outcome ("[Team]: UAT reconciliation in hours,
not days"); its body says what was measured, before and after, and links the Metrics row it moved.

## Finish by hand

1. **Before the page is published:** agree the method for every `Metrics` row and replace each `[N]`, `[Source]` and
   the *Hours given back* definition. A row whose method is still a placeholder stays off the page (filter the view on
   it, or leave the row out).
2. The Power BI report: build *Platform adoption* in the team's workspace (agent turns per week, reports shipped,
   teams on the platform) and give every viewer of this page access to it; the web part shows nothing to someone who
   cannot open the report.
3. Stories: add a Yes/No page property `Story` to the Site Pages library, then filter the News web part on it.
4. A scheduled flow refreshes `Metrics` weekly (writing `MetricValue` and `RefreshedOn`); until it exists, the owner
   updates the rows by hand on the first working day of the month.
5. Publish, and set the page description: "What the Data Czars platform gives back, and how it is counted."

## Check

- Every number on the page has a method row whose `Definition` and `Source` are not placeholders.
- The report loads for a partner who was given access, and not for one who was not.
