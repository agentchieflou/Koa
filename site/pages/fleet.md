# The fleet

**URL:** `SitePages/The-fleet.aspx`. **For:** everyone. **Design:** the canvas artboard *The fleet*.

The agents, one per repository, that work the team's Jira tickets, data-czars and usage_tool among them. The page
explains the fleet and embeds FleetAgent; the FleetAgent lists, flows and app are built from Koa's `build/` by the
session that owns them. FleetAgent's lists carry one or more operators' agents and approvals: they get their own
permissions, members only, before any web part points at them.

## Build it with Copilot

From any page, open **Copilot** and ask it to create a page, then paste (`site/out/pages/fleet.md` has it filled in):

```text
Create a page called "The fleet" for the Data Czars site. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

Title area: Image layout, topic header "How the team works", title "The fleet", and the description "{{fleet.summary}}"

1. Two-thirds left section, no background.
   Left: heading "The daily loop", then a numbered list:
   0. Start the day fresh. Every agent is listed with why it is ready or not; one confirm starts exactly the ready ones.
   1. Open the desk: one tile per repository.
   2. Hand out the work. Drag a ticket from the Jira board onto a tile.
   3. Work on something else. A tile turns amber when an agent wants to write to Jira, red when it needs a person, green when it is done.
   4. Answer. Approve the write, reply to the agent that asked, or read the sentence from the one that stopped.
   5. End the day: every Jira, Bitbucket and Confluence write in one table, on one confirm.
   Right: heading "Where intake meets the fleet", the text "A request raised on Get help becomes a Jira ticket only after one approval on the desk or the phone; the ticket then lands on the board the fleet works from.", and a Quick links web part, List layout: How the fleet works, Approvals, FleetAgent build sheet.
2. One-third right section, Neutral background. Left: a Microsoft PowerApps web part. Right: heading "The fleet on your phone", the text "FleetAgent shows what every agent needs and carries an approval or a reply back to the laptop, which checks the digest, the person and the expiry before it acts. The app decides nothing.", and a Button web part "Open FleetAgent".
3. One-column section, no background. Heading "Four ways to see it", then a Quick links web part, Grid layout, four links with images: The desk ("One tile per repository, every state in words and colour"), Chat ("Every agent's conversation, one column each"), The map ("Where each agent is in its ticket and its repository"), The world, lab ("One robot per agent: walk to the one that needs you").
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| title | Image layout | title area | background `assets/title-fleet.png` |
| 1 | Two-thirds left, none | Text, Quick links | links to this-next-please `docs/fleet.md`, `docs/fleet-approvals.md`, and Koa `build/README.md` |
| 2 | One-third right, Neutral | Microsoft PowerApps, Text, Button | the FleetAgent app id from Koa's build (`build/fleet.config.json`, `appId`); the button opens the app's web link |
| 3 | One column, none | Quick links, Grid | screenshots of `/`, `/chat`, `/map`, `/world` from a running desk |

## Words

All of it is in the prompt; the daily loop is this-next-please's `docs/fleet.md`, said for readers who do not run a
fleet, and `{{fleet.summary}}` is the fleet scan's one sentence.

## Finish by hand

1. PowerApps web part: paste the app id at the section's width (FleetAgent is a responsive Tablet app). Anyone who
   opens the page needs the app shared with them; others see a notice instead.
2. Screenshots for section 3: take them with no ticket text or data in view. Alt text names the view.
3. Publish, and set the page description: "The fleet: the agents, one per repository, that work the team's tickets."

## Check

- The app loads inside the page for a member who has opened FleetAgent once.
- Nothing on the page shows an operator's agents or approvals to someone outside the team.
