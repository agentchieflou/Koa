# Copilot in Edge: the facts on a Confluence page

The repository scans know the code. The team's Confluence pages know what a new user goes through: the access to
request, the setup, the errors people hit and their fixes. No Copilot connector reaches the team's Confluence yet
(`site/agents/README.md`, the asks for IT), but Microsoft 365 Copilot in Edge can read the page you have open. This
prompt asks it for that page's facts, as JSON the build reads. Run it once per page:

- the kernel's main page (what it is, the access to request, the setup);
- the common errors page;
- the onboarding pages for access and service accounts;
- the Spark configuration and profile pages;
- the page listing the package's contents.

1. Open the page in **Microsoft Edge**, signed in with your work account.
2. Open **Copilot** in Edge's sidebar, on the **Work** tab, and let it use the open page (the page-context option in
   the chat box). Whether your organisation allows that is row S14 in `site/README.md`; if it does not, select the
   page's text, copy it, and paste it under the prompt in Microsoft 365 Copilot instead.
3. Fill in the bracketed line, paste the whole prompt, and send it.
4. Check the answer against the page. Then save the JSON block as `site/local/context/wiki-<page>.json` in Koa (for
   example `wiki-kernel.json`, `wiki-common-errors.json`) and run `python site/provision.py context`. The `wiki-`
   files merge after the repository scans, so the repository wins where both say something and the pages fill what
   it leaves out.

```text
This is a page from my team's Confluence space. Using only what this page says (not the rest of the space, the web, or anything else you know), give me its facts for our SharePoint site as one JSON code block, and nothing else after it.

The page is about: [the kernel / its common errors / onboarding and access / Spark configuration and profiles / the package's contents]

The JSON has exactly these keys; leave out any key the page says nothing about:
{
  "kernel": {"name": "", "summary": "", "buildsOn": "", "includes": [], "connectsTo": [], "setupSteps": [], "firstSession": "", "docs": {"url": "", "desc": "Confluence"}},
  "access": [{"name": "", "why": "", "neededFor": "Using the kernel", "request": {"url": "", "desc": ""}}],
  "profiles": [{"name": "", "useWhen": "", "executors": "", "executorMemory": "", "executorCores": "", "driverMemory": "", "kind": "Standard"}],
  "faq": [{"question": "", "answer": "", "topic": "Common errors", "shownTo": "Everyone"}],
  "links": [{"title": "", "url": "", "category": "", "description": "", "shownTo": "Everyone"}],
  "gaps": []
}

Rules:
- kernel: only if the page is about the kernel. name as the page names it, without "the". docs.url is this page's address. setupSteps: the page's setup steps in order, one short sentence each, starting from the point the access is granted; commands exactly as written, screenshots left out. firstSession: the page's code to start Spark in a notebook, exactly as written.
- access: one entry per entitlement or permission the page says to request, its name exactly as written. neededFor is "Contributing code" when the page says it is needed only to fork, branch, push or open pull requests; otherwise "Using the kernel". why is what the page says it is for, in one sentence. request.url is the page's link for requesting it, if it gives one.
- profiles: only if the page lists Spark profiles or configurations by name. Numbers exactly as written; kind is "Specialized" for a profile outside the size ladder. useWhen is what the page says the profile is for, in one sentence.
- faq: each error the page lists, with the error as a person sees it (a few words) as the question and the page's fix as the answer, topic "Common errors". Questions about access get the topic "Access", about setup "Getting started".
- links: every link on the page a user of the kernel would follow: other onboarding pages, the repository, request forms. category is one of Confluence, Bitbucket, Jira, Power BI, Teams, SharePoint, Docs, Other; shownTo is "Members" for source code, otherwise "Everyone".
- Never include a password, token, key, a host name from a command, a user ID, a keytab or keyring path, a queue name, or anything about a customer. Leave out the names of the people who wrote or own the page.
- If the page says something the keys cannot hold, or something looks out of date, add one line to "gaps" saying what.
```

Check the profiles against the code before the site goes live: where the page and the session module disagree,
the module is right, and the page is the one to fix.
