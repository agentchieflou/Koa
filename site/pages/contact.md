# Contact

**URL:** `SitePages/Contact.aspx`. **For:** everyone. **Design:** the canvas artboard *Contact*.

The team, what to ask each person about, and one button per person that opens the way they prefer to be reached: a
Teams chat with a first line already typed, an email, a Teams call, or a meeting request. Each member sets their own
preference in the `Contacts` list, and their card follows it.

## Build it with Copilot

From any page, open **Copilot** and ask it to create a page, then paste (`site/out/pages/contact.md` has it filled in):

```text
Create a page called "Contact" for the Data Czars site. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

Title area: Image layout, topic header "Data Czars", title "Contact", and the description "The team, what to ask each of us about, and how each of us likes to be reached."

1. One-column section, no background. Heading "The team", then a List web part.
2. Two-column section, Neutral background.
   Left: heading "Not sure who?", the text "Ask the Czars in Copilot: it knows who handles what and opens their preferred way in. Or raise it on Get help and we route it.", and a Button web part "Get help" linking to Get-help.aspx.
   Right: heading "Keep your card current", the text "Team members: open the Contacts list and set your preferred method, working hours and what to ask you about. Your card's button follows your choice."
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| title | Image layout | title area | background `assets/title-contact.png` |
| 1 | One column, none | List | `Contacts`, view `Cards`; command bar off |
| 2 | Two columns, Neutral | Text, Button | |

## Words

All of it is in the prompt. The button on each card reads *Chat in Teams*, *Send an email*, *Call in Teams* or *Book a
meeting*: Teams links (`teams.microsoft.com/l/chat`, `/l/call`, `/l/meeting/new`) and `mailto:` built from the row's
email, which is all list formatting allows (`formatting/contacts-cards.json`).

## Finish by hand

1. Every member: open `Contacts`, find your row, and set **Preferred method**, **Working hours** and **Ask me about**;
   fill **Person** so the agent can match you to your account.
2. A member who should not be listed for partners: **For** = Members.
3. Publish, and set the page description: "The Data Czars team and the way each of us likes to be reached."

## Check

- Each card's button opens the right thing: a chat with the first line typed, a mail with the subject set, a call, or
  a new meeting with that person invited.
- Ask the site agent "Who should I ask about the usage reports?": it names the person and their preferred way.
