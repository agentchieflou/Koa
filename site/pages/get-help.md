# Get help

**URL:** `SitePages/Get-help.aspx`. **For:** everyone who uses a Data Czars product. **Design:** the canvas artboard
*Get help*.

Where people raise an issue with a supported product, or ask for work, an answer or access, and follow it to done.
Every submission is a row in the `Intake` list, made through its Microsoft Lists form, and becomes a ticket on the
team's Jira board (`site/intake/README.md`): the key, the link and the status come back to the row, so *My tickets*
always says where a request stands without anyone opening Jira.

## Build it with Copilot

From any page, open **Copilot** and ask it to create a page, then paste (`site/out/pages/get-help.md` has it filled in):

```text
Create a page called "Get help" for the Data Czars site. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

Title area: Image layout, topic header "Issues, requests, questions, access", title "Get help", and the description "Every request becomes a ticket on our Jira board, project {{jira.project}}. We triage within {{team.triageDays}} business days, and its status comes back here."

1. Two-column section, no background.
   Left: heading "Report an issue", the text "Something in a product we support is broken or wrong. Say what you did, what you expected and what happened; a screenshot helps.", and a Button web part "Report an issue".
   Right: heading "Request something", the text "A new report or a change, a question, or access to a product. Say who it is for and by when.", and a Button web part "Request something".
2. One-column section, Neutral background. Heading "What happens next", then an Image web part.
3. One-column section, no background. Heading "My tickets", then a List web part.
4. One-column section, no background. Heading "Questions people ask", then a List web part.
5. One-column section, no background. Heading "For the team", then a Quick links web part, List layout: Triage (the Intake list's Triage view), Open requests (the Open view), Jira board ({{jira.boardUrl}}).
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| title | Image layout | title area | background `assets/title-help.png` |
| 1 | Two columns, none | Text, Button ×2 | both buttons open the Intake form's link (Finish by hand 1) |
| 2 | One column, Neutral | Image | `assets/request-flow.png`; alt text below |
| 3 | One column, none | List | `Intake`, view `Mine`; command bar off |
| 4 | One column, none | List | `FAQ`, view `Everyone` |
| 5 | One column, none | Quick links, List | every link targeted to the Members group |

## Words

Alt text for the request-flow image: "What happens next. 1, Submit: the form on this page. 2, Jira ticket: it becomes a
ticket on our board within minutes. 3, Triage: within {{team.triageDays}} business days we take it, say when, or say
who can help instead. 4, Work: the status here follows the ticket. 5, Done: the row says so, with the ticket's last
word."

## Finish by hand

1. **The form.** Open the `Intake` list > **Forms** > **New form**: title "Get help from Data Czars", all of
   *What do you need?*, *Product*, *Title* (label it "In one line"), *Details*, *How much does it hurt?*, *Who is
   affected* and *Needed by*; branching that shows *How much does it hurt?* only for "Report an issue". Hide
   *Status*, *Jira*, *Jira link*, *Owner* and *Last sync*. Copy the form's link into both buttons. People who use
   the form never see the list.
2. **Who sees what.** Intake list settings > Advanced: *Read access* = items created by the user; *Create and edit*
   = items created by the user. Visitors get **Contribute** on this list only (stop inheriting on the list). Members
   keep full access.
3. **The Jira round trip**: `site/intake/README.md`, steps 1 to 4 (two flows and the laptop's `intake.py`).
4. Section 5's links: audience = the Members group on each.
5. Publish, and set the page description: "Report an issue or request work from Data Czars, and follow it in Jira."

## Check

- Signed in as a partner: the form submits, *My tickets* shows only your rows, and the team's links are hidden.
- A test issue gets its Jira key on *My tickets* after the laptop files it, and its status follows the ticket.
- The triage promise reads the same number here, on Home and in the FAQ.
