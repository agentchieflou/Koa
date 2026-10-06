# Copilot

**URL:** `SitePages/Copilot.aspx`. **For:** everyone; the last section is for the team. **Design:** the canvas
artboard *Copilot*.

How to work with Data Czars without leaving Microsoft Copilot: the agent in the site's header and in the Copilot app,
the agent in Teams chats, prompts that work, and what the team runs on a schedule. The agents themselves are
specified in `site/agents/`.

## Build it with Copilot

From any page, open **Copilot** and ask it to create a page, then paste (`site/out/pages/copilot.md` has it filled in):

```text
Create a page called "Copilot" for the Data Czars site. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

Title area: Image layout, topic header "Data Czars in Copilot", title "Copilot", and the description "Ask the Czars in SharePoint, in Teams and in Microsoft Copilot; prompts that work; and what the team runs on a schedule."

1. Two-thirds left section, no background.
   Left: heading "Ask the Czars", then a Text web part: "Ask the Czars answers from this site: the products and their status, the usage reports, how to get help, the links and who to ask. It cites what it used and never guesses. Open it from the Copilot button in this site's header, from the agents in Microsoft Copilot, or @mention it in a Teams chat or channel."
   Right: an Agent Link web part.
2. One-column section, Neutral background. Heading "Prompts that work", then a List web part.
3. Three-column section, no background.
   - Heading "In Teams": "Copy the agent's link for Teams and paste it in a chat or a channel; then @Ask the Czars answers there, for everyone in the conversation."
   - Heading "In Microsoft Copilot": "Three agents, under Agents in Microsoft Copilot: Ask the Czars for answers, Usage Analyst for questions about the usage reports, answered with the numbers, and Czars Desk to file an issue and follow your tickets."
   - Heading "On a schedule": "In Microsoft Copilot, schedule a prompt from the list above, such as what changed this month, and it arrives on its own."
4. One-column section, no background. Heading "For the team", then a Quick links web part, List layout: Czars Desk (the team's Copilot Studio agent), Scheduled prompts, Share a prompt to the team.
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| title | Image layout | title area | background `assets/title-copilot.png` |
| 1 | Two-thirds left, none | Text, Agent Link | Agent Link: *Ask the Czars* |
| 2 | One column, Neutral | List | `Prompts`, view `Library` |
| 3 | Three columns, none | Text ×3 | |
| 4 | One column, none | Quick links, List | every link targeted to the Members group; links to `site/agents/czars-desk.md` once it is published, and to Microsoft's pages on scheduled prompts and the Prompt Gallery |

## Words

All of it is in the prompt. The three agents and what each may do are in `site/agents/`: *Ask the Czars* (the site
agent), *Usage Analyst* (an Agent Builder agent in Microsoft Copilot) and *Czars Desk* (a Copilot Studio agent with
tools, for when the team has Copilot Studio).

## Finish by hand

1. Build the agents first (`site/agents/README.md`), so the Agent Link has something to point at.
2. Section 4: audience = the Members group on each link.
3. Publish, and set the page description: "Data Czars in Microsoft Copilot: the agents, the prompts, the schedules."

## Check

- The Agent Link opens Ask the Czars; @mentioning it in a Teams chat answers there.
- Each prompt in the list works as written, with the brackets filled in.
