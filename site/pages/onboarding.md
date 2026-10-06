# Onboarding

**URL:** `SitePages/Onboarding.aspx`. **For:** members; the page's own permissions limit it to the Members group.
**Design:** follows the canvas's *Team* artboard; it is the page *Start onboarding* opens.

A new Czar's first day, week and month on one page, with the path to take and the questions others asked.

## Build it with Copilot

From any page, open **Copilot** and ask it to create a page, then paste:

```text
Create a page called "Onboarding" for the Data Czars site. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

Title area: Plain layout, title "Onboarding", and the description "Your first day, week and month as a Data Czar."

1. Two-thirds left section, no background. Left: the text "Welcome. Work down the list in order; your buddy checks in at the end of each phase. Anything unclear is a question for office hours, and a fix for this page." then heading "Your checklist" and a List web part. Right: heading "Your buddy" and a People web part, Compact layout, then heading "Start with 101" and a List web part.
2. One-column section, Neutral background. Heading "Questions new Czars ask", then a List web part.
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| 1 | Two-thirds left, none | Text, List | `Onboarding`, view `All Items`: one running step number, Phase beside it |
| 1 | right column | People, List | the buddy for the current joiner; `LearningPaths`, view `101` |
| 2 | One column, Neutral | List | `FAQ`, view `Members` |

## Words

All of it is in the prompt.

## Finish by hand

1. Page permissions: this page only. Site Pages > the page > Manage access > stop inheriting > remove Visitors.
   (Members already have it.) The mega menu link is targeted to Members as well.
2. People: the buddy for whoever is joining; change it for the next joiner.
3. Publish, and set the page description: "Onboarding for new Data Czars: first day, week and month."

## Check

- Signed in as a partner, the page is not reachable and its menu link is not shown.
- The checklist reads in the order Day one, Week one, Month one.
