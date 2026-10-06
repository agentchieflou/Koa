# Team

**URL:** `SitePages/Team.aspx`. **For:** everyone; the Members links are targeted to the site's Members group.
**Design:** the canvas artboard *Team*.

Who we are, how we work, who answers what, and what we decided. The decision log is public on purpose: partners
building on the platform should see why it works the way it does.

## Build it with Copilot

From any page, open **Copilot** and ask it to create a page, then paste:

```text
Create a page called "Team" for the Data Czars site. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

Title area: Image layout, topic header "Who we are", title "Team", and the description "A tools and platform team. We build what makes the bank's data work fast and safe, then we run it."

1. Two-thirds left section, no background. Left: heading "How we work", then a Text web part with six short paragraphs, each starting with its title in bold:
   - The operator decides. Agents do the busywork. Every write to Jira, Bitbucket or Confluence waits for a person.
   - Cheap models, strong rails. Skills, refusals and tests make a small model dependable, so the bill stays small too.
   - Bytes are exact. What ships is what was reviewed: pinned contracts, checked digests, no silent rewrites.
   - Never loosen a test. A red test is a finding. We fix the cause, never the assertion.
   - "Not yet measured" is an answer. What only a laptop, a tenant or a phone can prove stays unclaimed until someone ran it and wrote it down.
   - Words carry status. Colour helps; the word decides. Every state is readable without seeing colour.
   Right: heading "People" and a People web part, Descriptive layout.
2. One-column section, Neutral background. Heading "Who to ask", then a List web part.
3. Two-thirds left section, no background. Left: heading "Decisions" and a List web part. Right: heading "For members", a Quick links web part, List layout, with Onboarding, Team calendar, Notebook and Team channel, then a Call to action web part: "New to the team? Day one, week one and month one, with a buddy for each." with the button "Start onboarding" linking to Onboarding.aspx.
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| title | Image layout | title area | background `assets/title-team.png` |
| 1 | Two-thirds left, none | Text, People | People: every member, with their role from the design (Platform lead, Agents and the fleet, Power BI tooling, Data connectors, UAT and testing, Document AI) |
| 2 | One column, Neutral | List | `WhoToAsk`, view `All Items`; command bar off |
| 3 | Two-thirds left, none | List | `Decisions`, view `Log` |
| 3 | right column | Quick links, Call to action | Quick links audience: Members group, per link; CTA to Onboarding.aspx |

## Words

All of it is in the prompt. The six principles are the team's; edit them here first, then on the page, so the agent
and the page say the same thing.

## Finish by hand

1. People: add each member and their role.
2. WhoToAsk: fill `Contact` and `Backup` for every row (the starter rows have the topics only).
3. Quick links: turn on audience targeting in the web part, then set each link's audience to the site's Members
   group. Team calendar opens the group calendar; Notebook opens the site's OneNote; Team channel opens the Teams
   channel.
4. Publish, and set the page description: "The Data Czars team: how we work, who to ask, what we decided."

## Check

- Signed in as a partner: the four member links are not shown; the decision log is.
- Every topic in Who to ask names a person and a backup.
