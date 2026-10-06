# Work with us

**URL:** `SitePages/Work-with-us.aspx`. **For:** partners across the bank first, then members.
**Design:** the canvas artboard *Work with us*.

The page a partner lands on from anywhere: how to engage, how a request moves, where their own requests stand, what
we are building, and the questions everyone asks.

## Build it with Copilot

From any page, open **Copilot** and ask it to create a page, then paste:

```text
Create a page called "Work with us" for the Data Czars site. Use only the sections and web parts below, in this order, and use my words exactly. Propose the layout first and wait for my go-ahead.

Title area: Image layout, topic header "For partners across the bank", title "Work with us", and the description "Bring us a data problem. Within [N] business days you hear whether we can take it, who owns it and when it lands."

1. Three-column section, no background, heading "How we engage". In each column a Text web part and a Button web part:
   - Consult. "Talk it through." "Thirty minutes at office hours, no ticket needed. You leave with a plan, a tool to try or the right team to call." Button "Book office hours".
   - Build. "Build it with us." "A report, a pipeline or an automation, built on the platform with you, tested, and handed over with its runbook." Button "Request work".
   - Enable. "Run it yourself." "We set your team up on the CLI, the skills and the fleet, and stay close for your first sprint." Button "Onboard your team".
2. One-column section, Neutral background. Heading "How a request moves", then an Image web part.
3. One-third left section, no background. Left: heading "Request work", the text "One form for reports, data pulls, automation, tool access and UAT support. Tell us who will use it and by when; we do the rest.", and a Button web part "Request work". Right: heading "My requests" and a List web part.
4. Three-column section, Soft background, heading "Roadmap". A List web part in each column, titled Now, Next and Later.
5. One-third left section, no background. Left: heading "Office hours" and an Events web part, Compact layout. Right: heading "Questions people ask" and a List web part.
```

## Sections

| # | Section | Web part | Source and settings |
| --- | --- | --- | --- |
| title | Image layout | title area | background `assets/title-work-with-us.png` |
| 1 | Three columns, none | Text, Button ×3 | buttons: Office hours anchor, Request work anchor, Onboarding page (members) or office hours (partners) |
| 2 | One column, Neutral | Image | `assets/request-flow.png`; alt text below |
| 3 | One-third left, none | Text, Button | the button opens `Lists/Requests/NewForm.aspx` |
| 3 | right column | List | `Requests`, view `Mine`; command bar off |
| 4 | Three columns, Soft | List ×3 | `Roadmap`, view `Now`; `Roadmap`, view `Next`; `Roadmap`, view `Later` |
| 5 | One-third left, none | Events | category Office hours, Compact, 3 events |
| 5 | right column | List | `FAQ`, view `Partners` |

## Words

Alt text for the request-flow image, which is also its long description: "How a request moves. 1, Submit: one form;
who uses it, what decision it serves, by when. 2, Triage: within [N] business days, yes, not yet, or who to ask
instead. 3, Plan: an owner, a Jira ticket and a date you can hold us to. 4, Build: on the platform, with agents doing
the busywork and tests on every change. 5, Ship and measure: handed over with a runbook, then counted on the Impact
page."

## Finish by hand

1. **Requests permissions, before the page is shared with partners.** List settings > Advanced settings: *Read
   access* = Read items that were created by the user; *Create and Edit access* = Create items and edit items that
   were created by the user. Then give the site's Visitors group **Contribute** on this list only (Permissions for
   this list > Stop inheriting > grant). Members keep full access through the Members group.
2. The Requests form: in the list, **New** > **Edit form** > **Edit columns**: hide `Status`, `Owner` and `JiraKey`
   from the new form, so partners fill only what is theirs.
3. Optional, members only: a **Board** view of Requests grouped by `Status` (New view > Board), for triage.
4. Image web part: upload `assets/request-flow.png` and paste the alt text above.
5. Publish, and set the page description: "How to work with Data Czars: engage, request work, follow it."

## Check

- Signed in as a partner (a Visitors member): you can add a request, see only your own, and cannot change its Status.
- The FAQ shows only the Partners rows.
- The triage promise reads the same number here, on Home and in the FAQ.
