# The fleet

**URL:** `SitePages/The-fleet.aspx`. **For:** everyone. **Design:** the canvas artboard *The fleet*.

**Shared with the fleet session.** The FleetAgent lists, flows and app are built from Koa's `build/` by the session
that owns them. This page shows them; it creates none of them. Which FleetAgent data appears here (the app only, or
also its lists) is that session's call, because the five lists carry one operator's agents and approvals: they get
their own permissions, members only, before any web part points at them.

## Build it with Copilot

From any page, open **Copilot** and ask it to create a page, then paste:

```text
Create a page called "The fleet" for the Data Czars site. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

Title area: Image layout, topic header "Agent platform", title "The fleet", and the description "Several headless agents, one per repository, watched from one window. The fleet answers the one question none of them can: which of these needs me right now?"

1. Two-thirds left section, no background.
   Left: heading "The daily loop", then a numbered list:
   0. Start the day fresh. ad-fleet fresh --all --dry-run lists every agent and why; --confirm starts exactly the ticked rows, one turn each.
   1. Open the desk. ad-fleet open, or serve --open: one tile per registered repository.
   2. Hand out the work. Press b for your Jira board and drag a ticket onto a tile, or start it on a repository.
   3. Work on something else. A tile turns amber when an agent wants to write to Jira, red when it needs you, green when it is done. The first two send a toast.
   4. Answer. Approve the write from the tile, reply to the agent that asked, read the sentence from the one that stopped.
   5. End the day. ad-fleet wrapup --all --day --dry-run, then --confirm: every Jira, Bitbucket and Confluence write in one table, on one confirm.
   Right: a Code snippet web part, language PowerShell, with these four lines:
   ad-fleet repo add C:/repos/rdsd-pbi-reporting
   ad-fleet serve --open
   ad-fleet start rdsd-pbi-reporting RDSD-101
   ad-fleet status
   and under it a Quick links web part, List layout: How the fleet works, Approvals, Notifications, Jira intake, FleetAgent build sheet.
2. One-third right section, Neutral background. Left: a Microsoft PowerApps web part. Right: heading "The fleet on your phone", the text "FleetAgent shows what every agent needs and carries your approval or reply back to the laptop, which checks the digest, your identity and the expiry before it acts. The app decides nothing.", and a Button web part "Open FleetAgent".
3. One-column section, no background. Heading "Four ways to see it", then a Quick links web part, Grid layout, four links with images: The desk ("One tile per repository, every state in words and colour"), Chat ("Every agent's conversation, one column each"), The map ("Where each agent is in its ticket and its repository"), The world, lab ("A wet plaza, one robot per agent: walk to the one that needs you").
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| title | Image layout | title area | background `assets/title-fleet.png` |
| 1 | Two-thirds left, none | Text, Code snippet, Quick links | links to this-next-please `docs/fleet.md`, `docs/fleet-approvals.md`, `docs/fleet-notifications.md`, `docs/fleet-intake.md`, and Koa `build/README.md` |
| 2 | One-third right, Neutral | Microsoft PowerApps, Text, Button | the FleetAgent app id from Koa's build (`build/fleet.config.json`, `appId`); border off; the button opens the app's web link |
| 3 | One column, none | Quick links, Grid | images: screenshots of `/`, `/chat`, `/map`, `/world` from a running desk |

## Words

All of it is in the prompt, taken from this-next-please's `docs/fleet.md` and Koa's README. When the daily loop
changes there, change it here in the same week.

## Finish by hand

1. PowerApps web part: paste the app id; leave it at the section's width so the app shows its tablet layout (it is a
   responsive Tablet app; `powerapp/` in Koa). Anyone who opens the page needs the app shared with them.
2. Quick links in section 1: point each link at its doc, opened in a new tab.
3. Quick links in section 3: take the four screenshots on a laptop running `ad-fleet serve --open`, with no ticket
   or customer data in view, and upload them. Alt text names the view.
4. Publish, and set the page description: "The fleet: several agents, one per repository, watched from one window."

## Check

- The app loads inside the page for a member who has opened FleetAgent once.
- Nothing on the page shows another person's agents to someone outside the team.
