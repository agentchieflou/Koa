# The Data Czars site: the build sheet

Everything needed to build `OSP-Data-Czars`, the SharePoint site for Data Czars and the tooling it supports in the
PAE: the facts gathered from the team's own repositories, the lists and their formatting, the pages, the intake that
files Jira tickets, the usage reports' library, and the agents that put all of it in Microsoft Copilot. Read
`DESIGN.md` first for what the site is and why.

```
site/
  DESIGN.md                    the design: audiences, principles, navigation, pages, Copilot, visual system, permissions
  README.md                    this build sheet
  context.example.json         the shape of what the scans find (made-up values; tests use it)
  czars.code-workspace         VS Code: Koa, data-czars, usage_tool and this-next-please side by side, for the scans
  prompts/m365-org-facts.md    the prompt for Microsoft Copilot: the team's people, channels and spaces
  prompts/confluence-page-facts.md   the prompt for Copilot in Edge, one Confluence page at a time
  site.json                    the navigation, the pages and the lists each one shows, the look
  lists.json                   every list: columns, views, formatting, the starter rows that hold no internal fact
  LISTS.md                     lists.json in words, with a Copilot prompt per list (generated: provision.py docs)
  formatting/*.json            column, gallery and row formatters
  provision.py                 the context, site scripts, flows, the console script, the filled-in pages
  pages/*.md                   one sheet per page: Copilot prompt, sections, words, finishing, check
  intake/                      Intake <-> Jira through the laptop (intake.py), and the usage reports' landing
  agents/                      Ask the Czars, Usage Analyst, Czars Desk, and the Teams wiring
  skills/data-czars-pages/     the site's Copilot skill
  assets/                      the mark and the artwork, SVG and PNG, and the script that draws them
  local/, out/                 git-ignored: what the scans found, and everything made from it
.github/prompts/czars-*.prompt.md   the scans and the build, for a Copilot agent
.github/skills/build-czars-site/    the skill the build follows
```

**Koa is public; the team's facts are not.** The scans write only to `site/local/`, and everything made from them
lands in `site/out/`; git ignores both. Tracked files hold the structure and the wording, never an internal address,
a colleague's name or a product's internals, and `tests/test_site.py` refuses them.

## Who does what

| Step | Who | Time |
| --- | --- | --- |
| 0. The facts | a Copilot agent scans the repositories; Copilot in Edge reads the Confluence pages; Microsoft Copilot knows the people | 30 min |
| 1. The look | a site owner, by hand | 10 min |
| 2. The lists | a Copilot agent through the provisioning flow, or a site owner through the console | 5 min |
| 3. The site skill | a site owner, in Copilot in SharePoint | 2 min |
| 4. The navigation | Copilot in SharePoint, from the prompt below | 5 min |
| 5. The pages | Copilot in SharePoint, one sheet at a time; a site owner finishes each | 10 min a page |
| 6. Intake and reports | a Copilot agent creates three flows; the laptop runs `intake.py` | 20 min |
| 7. Copilot and Teams | the team | 30 min |
| 8. Permissions | a site owner | 10 min |

You need: **Owner** on the site; a **Microsoft 365 Copilot** licence for steps 3 to 5 and 7; Power Automate with the
Standard connectors for steps 2 and 6; the this-next-please CLI on the laptop for step 6. No step needs a tenant admin;
`agents/README.md` lists the four things an admin could add later.

## 0. The facts

Koa, `data-czars` and `usage_tool` sit side by side in one folder. A Copilot agent reads the two repositories and the
fleet, Copilot in Edge reads the team's Confluence pages, and Microsoft Copilot answers for the people; each writes
one file under `site/local/context/`.

1. **Open them together.** VS Code: **File** > **Open Workspace from File** > `site/czars.code-workspace`. Copilot CLI:
   start it in the folder that holds all three.
2. **Run the scans**, in Copilot's agent mode, one at a time: `/czars-scan-data-czars`, `/czars-scan-usage-tool`,
   `/czars-scan-fleet` (in Copilot CLI: "Follow `.github/prompts/czars-scan-data-czars.prompt.md`", and so on). Each
   reads only, never runs the code, and ends by naming its gaps.
3. **Ask Microsoft Copilot** with `site/prompts/m365-org-facts.md`; save its answer as `site/local/context/org.json`.
   Then, for each Confluence page the prompt `site/prompts/confluence-page-facts.md` lists (the kernel's page, its
   common errors, onboarding and Spark configuration pages), open the page in Edge and run that prompt in Copilot's
   sidebar; save each answer as `site/local/context/wiki-<page>.json`. The repository wins where both say something;
   the pages fill what it leaves out, which is usually the access to request and the setup steps.
4. **Your own answers.** Write what only the team decides, and anything a scan got wrong or left as a gap, to
   `site/local/context/00-operator.json`, for example
   `{"site": {"url": "https://<tenant>.sharepoint.com/sites/OSP-Data-Czars"}, "team": {"triageDays": "3"}}`.
   The files merge in name order and the first value found wins, so yours, named `00-`, overrides every scan.
5. `python site/provision.py context` merges them into `site/local/context.json`, says what it found, and names every
   gap left, including every fact a page or an agent still needs. Repeat 4 and 5 until it names none.

## 1. The look

Settings (the gear):

1. **Site information**: Site name `Data Czars`; Site description from `site.json`.
2. **Change the look** > **Theme**: *Teal* (DESIGN.md, Visual system). If your organisation's brand theme appears
   under *From your organization*, use it and redraw the artwork with `python site/assets/make_assets.py --accent
   "#RRGGBB"`, then re-render the PNGs.
3. **Change the look** > **Header**: layout *Standard*, background *None*; Site logo and thumbnail `assets/logo.png`.
4. **Change the look** > **Navigation**: *Horizontal*, menu style *Mega menu*. Then **Site navigation** > **Edit** >
   turn on **Enable site navigation audience targeting**.

## 2. The lists

Nine lists and one library (`LISTS.md`), with their columns, views, formatting and starter rows: the products, access,
Spark profiles, links, contacts, releases and questions the scans found, plus the questions and prompts every Data
Czars site starts with.
Every way below is safe to run again.

**A. A Copilot agent.** With the `power-automate` plugin installed (`build/README.md` §2), say: *Build the Data Czars
lists. Use the build-czars-site skill.* It runs `python site/provision.py flow`, creates the one-shot flow
`CzarsProvisionSite`, runs it twice, checks every outcome, and deletes it.

**B. The browser console.** `python site/provision.py console` writes `site/out/provision.console.js`. Open the site
signed in as an owner, open the developer tools (F12) > **Console**, paste the file, press Enter. It prints one line
per list and per row and ends with `done`.

**C. By hand with Copilot.** `LISTS.md` has a Copilot prompt per list and what to finish by hand.

A and B call SharePoint's `ExecuteTemplateScript`, the endpoint PnP PowerShell's `Invoke-PnPSiteScript` uses, which
applies a site script with only your own rights on the site. It is not in Microsoft's REST reference, so the first run
is row S1 below. If it is refused, `python site/provision.py scripts` writes the scripts for a SharePoint admin to
register once as a site template, which you then apply from **Settings** > **Apply a site template**.

## 3. The site skill

Open **Copilot** on the home page (not in edit mode), paste
`Create a site skill named data-czars-pages from the following definition, exactly as written, and save it as a site skill for this site.`
followed by the whole of `skills/data-czars-pages/SKILL.md`, review the draft, and confirm. It is saved as
`/Agent Assets/Skills/data-czars-pages/SKILL.md`; from then on Copilot loads it whenever someone builds or edits here.

## 4. The navigation

In **Copilot** on the home page, paste:

```text
Build this site's navigation. Keep it horizontal with a mega menu, remove the links that are there now (Notebook, Documents, Pages, Site contents and Recycle bin stay reachable from Settings), and create exactly these, in this order. Each label links to its page; each group heading is a label without a link; each link goes to the page and anchor given. Propose it first and wait for my go-ahead.

Home: Home.aspx
Get started: Get-started.aspx
  Get started: What you get (#what-you-get), Get access (#get-access), Set up (#set-up), Your first session (#your-first-session), Pick a profile (#pick-a-profile), Common errors (#common-errors)
Products: Products.aspx
  Products: Product catalog (#product-catalog), Status (#status), What's new (#releases)
Usage reports: Usage-reports.aspx
  Reports: Latest reports (#latest-reports), All reports (#all-reports), About the usage tool (#about-the-usage-tool)
Get help: Get-help.aspx
  Get help: Report an issue (#report-an-issue), Request something (#request-something), My tickets (#my-tickets), FAQ (#questions-people-ask)
  For the team: Triage (#for-the-team), Jira board (our Jira board's address)
Links: Links.aspx
Contact: Contact.aspx
The fleet: The-fleet.aspx
Copilot: Copilot.aspx
  Copilot: Ask the Czars (#ask-the-czars), Prompts that work (#prompts-that-work), In Teams (#in-teams)
```

Then target the **For the team** heading and its links to the site's Members group (**Edit** > the link's **...** >
**Edit** > *Audiences to target*). If Copilot refuses links to pages that do not exist yet, do this after step 5.

## 5. The pages

`python site/provision.py pages` writes every sheet in `pages/` to `site/out/pages/` with the scanned facts filled in.
Build them in this order, so every link a page makes has somewhere to go: `get-help`, `get-started`, `products`,
`usage-reports`, `links`, `contact`, `fleet`, `copilot`, then `home`. For each:

1. Upload the page's images from `assets/` to **Site Assets**.
2. Paste the filled-in prompt into Copilot as the sheet says; check the proposal against the sheet's *Sections*
   table; let it build.
3. Do the sheet's *Finish by hand*, publish, and run its *Check*.

The design canvas shows each page as it should look; **Blueprint** in an artboard's Tweaks names the web part behind
every block.

## 6. Intake and reports

`intake/README.md`: the folders, the three flows (`python site/provision.py flows --results-folder-id <id>`, created
by the build-czars-site skill), and the first ticket through `python site/intake/intake.py`.

## 7. Copilot and Teams

`agents/README.md`: Ask the Czars (the site agent), Usage Analyst (Microsoft Copilot), Czars Desk (Copilot Studio),
the Teams channel's tabs and posts, and the Copilot features the team uses. The filled-in instructions are in
`site/out/agents/` after step 5's `pages` command.

## 8. Permissions

1. Partners join the site's **Visitors** group (or a security group of them), never Members.
2. `Intake`: item-level permissions, and Visitors' Contribute on that list only (`pages/get-help.md`).
3. `UsageReports`: inherits the site; narrow it if usage may be seen only by some (`pages/usage-reports.md`).
4. FleetAgent's lists, when the fleet session puts them here: their own permissions, members only.

## What only the tenant can prove

Every row reads *not yet measured* until someone runs it on the tenant. Record each run, with the date and what you
saw, in this-next-please's `docs/windows-verification.md`, in a §Site section beside §Mobile, and change the row here
in the same pull request.

| Row | What | How to see it | Result |
| --- | --- | --- | --- |
| S1 | `ExecuteTemplateScript` applies the scripts with site-owner rights only | step 2, A or B: every list exists | not yet measured |
| S2 | `addSPView` with `viewType2: TILES` and `formatterJSON` makes the gallery views | Products > Catalog shows cards | not yet measured |
| S3 | `setSPFieldCustomFormatter` formats Status and Support | Products > All Items shows pills | not yet measured |
| S4 | the starter rows land (item types `SP.Data.<List>ListItem`) | Products has one row per scanned product | not yet measured |
| S5 | Copilot builds each page from its filled-in prompt | each sheet's *Check* | not yet measured |
| S6 | Copilot builds the mega menu from step 4's prompt | the menu matches `site.json` | not yet measured |
| S7 | the site skill loads when someone edits a page | the skill card in Copilot's reply | not yet measured |
| S8 | Ask the Czars answers its check questions with citations | `agents/ask-the-czars.md` §Check | not yet measured |
| S9 | Usage Analyst computes from the report files it names | `agents/usage-analyst.md` §Check | not yet measured |
| S10 | Czars Desk files a request as the person and lists only theirs | `agents/czars-desk.md` §Check | not yet measured |
| S11 | a form submission reaches the laptop as `intake-<id>.json` | `intake/README.md`, set it up 4 | not yet measured |
| S12 | a result file merges the Jira key and status into its row | *My tickets* shows the key | not yet measured |
| S13 | a report copied into `<type>/<yyyy-mm>/` is tagged within the hour | *Latest reports* shows it | not yet measured |
| S14 | Copilot in Edge reads the open Confluence page (page context allowed on this tenant) | step 0, 3: the answer quotes the page | not yet measured |

## Changing the site later

The repository comes first. Change `lists.json` (then `python site/provision.py docs` and step 2 again), a sheet in
`pages/`, `site.json`, the skill or an agent; run `python -m pytest -q`; open a pull request; then apply it to the
site. When the code in data-czars or usage_tool changes, run its scan again and `python site/provision.py context`:
the new products, releases and links become rows the next time step 2 runs. Running the provisioning again adds
columns and views, updates formatting and choices, and adds missing rows; it never deletes anything.
