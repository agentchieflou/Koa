# Microsoft 365 Copilot: the team's people and places

The repository scans know the code. They do not know who is on the team, how each person likes to be reached, or
where the team's Teams channel and Confluence space are. Microsoft 365 Copilot does: it sees the directory, Teams
and SharePoint as you do. This prompt asks it for exactly those facts, as JSON the build reads.

1. Open **Microsoft 365 Copilot** (the desktop app or m365.cloud.microsoft) on the **Work** tab, signed in as yourself.
2. Fill in the two bracketed lines, paste the whole prompt, and send it.
3. Check the answer. Delete anyone who should not be listed, and fix any title. Then save the JSON block as
   `site/local/context/org.json` in Koa and run `python site/provision.py context`.

```text
I'm building the SharePoint site for my team, Data Czars. Using only what you can see in our organization (the directory, Teams, SharePoint and my email and calendar), give me facts about the team as one JSON code block, and nothing else after it.

The team members are: [names, separated by commas]
Our Teams team or channel is called: [name, or "find it"]

The JSON has exactly these keys:
{
  "contacts": [{"name": "", "email": "", "role": "", "topics": "", "preferredMethod": "Teams chat", "workingHours": "", "shownTo": "Everyone"}],
  "links": [{"title": "", "url": "", "category": "", "description": "", "shownTo": "Everyone"}],
  "team": {"officeHours": ""},
  "jira": {"boardUrl": ""},
  "gaps": []
}

Rules:
- contacts: one entry per team member I named, in that order. name and email from the directory; role is their job title; topics is two to five things colleagues come to them for, judged from what they work on in Teams and SharePoint, in a few words each. preferredMethod stays "Teams chat"; each person sets their own on the site. Leave workingHours "".
- links: the web links to our Teams team and channels (category "Teams"), our Confluence space or spaces ("Confluence"), our Jira board ("Jira"), any SharePoint sites or Power BI workspaces the team owns ("SharePoint" or "Power BI"). Only links you can see; one-sentence descriptions.
- team.officeHours: if I or the team have a recurring meeting open to other teams (office hours, a clinic, a drop-in), say when and where in one sentence; otherwise "".
- jira.boardUrl: our team's Jira board, if you can see one; otherwise "".
- Never include anything from a private chat or an email body, any customer or account information, or anyone I did not name.
- For anything you cannot find, leave it "" and add one line to "gaps" saying what is missing.
```

Every member then opens **Contact** on the site and sets their own **Preferred method** (Teams chat, Email, Teams call
or Book a meeting) and working hours; the build only seeds the first answer.
