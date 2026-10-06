# The Data Czars site: the build sheet

Everything needed to build `OSP-Data-Czars`, the Data Czars SharePoint site, from this folder: the lists and their
formatting, the pages, the navigation, the site's Copilot skill and its agent. Read `DESIGN.md` first for what the
site is and why it looks the way it does.

```
site/
  DESIGN.md                    the design: audiences, principles, navigation, pages, visual system, permissions
  README.md                    this build sheet
  site.json                    the navigation tree, the pages and the lists each one shows, the look
  lists.json                   every list: columns, views, formatting, starter rows
  LISTS.md                     lists.json in words, with a Copilot prompt per list (generated: provision.py docs)
  formatting/*.json            column, gallery and row formatters the lists use
  provision.py                 lists.json -> site scripts, a provisioning flow, or a console script
  pages/*.md                   one sheet per page: Copilot prompt, sections, words, finishing, check
  skills/data-czars-pages/     the site's Copilot skill
  agent/ask-the-czars.md       the site agent
  assets/                      the mark and the artwork, SVG and PNG, and the script that draws them
```

## Who does what

| Step | Who | Time |
| --- | --- | --- |
| 1. The look | a site owner, by hand | 10 min |
| 2. The lists | a Copilot agent through the provisioning flow, or a site owner through the console | 5 min |
| 3. The site skill | a site owner, in Copilot in SharePoint | 2 min |
| 4. The navigation | Copilot in SharePoint, from the prompt below | 5 min |
| 5. The pages | Copilot in SharePoint, one sheet at a time; a site owner finishes each | 15 min a page |
| 6. The agent | a site owner | 10 min |
| 7. Permissions and sharing | a site owner | 10 min |

You need: **Owner** on the site; a **Microsoft 365 Copilot** licence for steps 3 to 6 (Copilot in SharePoint has been
rolling out since 30 September 2026); for step 2, either Power Automate (the flow) or the browser's developer
console (the console script). No tenant admin is needed for any step.

## 1. The look

Settings (the gear):

1. **Site information**: Site name `Data Czars`; Site description from `site.json`.
2. **Change the look** > **Theme**: *Teal* (DESIGN.md, Visual system). If your organisation's brand theme appears
   under *From your organization*, use it instead and redraw the artwork with
   `python site/assets/make_assets.py --accent "#RRGGBB"` (its primary colour), then re-render the PNGs.
3. **Change the look** > **Header**: layout *Standard*, background *None*; Site logo and Site logo thumbnail:
   `assets/logo.png`; site title visible.
4. **Change the look** > **Navigation**: *Horizontal*, menu style *Mega menu*. Then **Site navigation** > **Edit** >
   turn on **Enable site navigation audience targeting**.

## 2. The lists

Twelve lists and one library (`LISTS.md`), each with its columns, views, formatting and starter rows. Make them in
one of three ways; every way is safe to run again.

**A. A Copilot agent (the way the FleetAgent build works).** In Copilot CLI or VS Code agent mode, with the
`power-automate` plugin installed (`build/README.md` §2), say: *Build the Data Czars lists. Use the build-czars-site
skill.* It runs `python site/provision.py flow --site <url>`, creates the one-shot flow `CzarsProvisionSite`, runs it,
checks every outcome, and deletes the flow.

**B. The browser console.** `python site/provision.py console --site https://<tenant>.sharepoint.com/sites/OSP-Data-Czars`
writes `site/out/provision.console.js`. Open the site signed in as an owner, open the developer tools (F12) >
**Console**, paste the whole file, press Enter. It prints one line per list and per starter row and ends with `done`.

**C. By hand with Copilot.** Where neither A nor B is allowed, `LISTS.md` has a Copilot prompt for each list and says
what to finish by hand. Make them in the order listed: a lookup needs its target list first.

Both A and B call SharePoint's `ExecuteTemplateScript`, the endpoint PnP PowerShell's `Invoke-PnPSiteScript` uses,
which applies a site script to the site you are on with only your own permissions on it. It is not in Microsoft's
REST reference, so the first run is S1 below. If it is refused, `python site/provision.py scripts` writes the twelve
scripts, and a SharePoint admin can register them once as a site template (`Add-SPOSiteScript`, `Add-SPOSiteDesign`)
that you then apply from **Settings** > **Apply a site template**.

Then, by hand: the **Requests** permissions and form (`pages/work-with-us.md`, *Finish by hand* 1 and 2), and the
`Contact` and `Backup` of every **WhoToAsk** row.

## 3. The site skill

Open **Copilot** on the home page (not in edit mode) and paste:

```text
Create a site skill named data-czars-pages from the following definition, exactly as written, and save it as a site skill for this site.
```

followed by the whole of `skills/data-czars-pages/SKILL.md`. Review the draft it shows, then confirm. It is saved as
`/Agent Assets/Skills/data-czars-pages/SKILL.md`; you can also upload the file there directly. From now on Copilot
loads it whenever someone builds or edits on this site.

## 4. The navigation

In **Copilot** on the home page, paste:

```text
Build this site's navigation. Keep it horizontal with a mega menu, remove the links that are there now (Notebook, Documents, Pages, Site contents, Recycle bin stay reachable from Settings), and create exactly these, in this order. Each label links to its page; each group heading is a label without a link; each link goes to the page and anchor given. Propose it first and wait for my go-ahead.

Home: Home.aspx
Platform: Platform.aspx
  Tools: Tool catalog (Platform.aspx#tool-catalog), Getting started (Platform.aspx#get-started-in-four-commands), Status (Platform.aspx#status), What's new (Platform.aspx#releases)
  Agent platform: The fleet (The-fleet.aspx), FleetAgent on your phone (The-fleet.aspx#the-fleet-on-your-phone), Skills library (Platform.aspx#skills-library), The world (lab) (The-fleet.aspx#four-ways-to-see-it)
  Data and BI: Power BI toolkit, Data connectors, UAT reconciliation, Document AI (each Platform.aspx#tool-catalog)
Work with us: Work-with-us.aspx
  Engage: Services (#how-we-engage), Request work (#request-work), My requests (#my-requests)
  Plan: Roadmap (#roadmap), Office hours (#office-hours), FAQ (#questions-people-ask)
Learn: Learn.aspx
  Paths: 101: your first week, 201: running a fleet, 301: building skills (each Learn.aspx#learning-paths)
  Library: Guides and runbooks (#guides-and-runbooks), Standards (#standards), Demos and recordings (#demos-and-recordings), Glossary (#glossary)
Team: Team.aspx
  About: Mission and principles (#how-we-work), People (#people), Who to ask (#who-to-ask)
  Members: Onboarding (Onboarding.aspx), Decisions (Team.aspx#decisions), Team calendar (the group calendar), Notebook (the site notebook)
Impact: Impact.aspx
```

Then, by hand, target the **Members** heading and its four links to the site's Members group (**Edit** > the link's
**...** > **Edit** > *Audiences to target*). Build the navigation after the pages (step 5) if Copilot refuses links
to pages that do not exist yet.

## 5. The pages

One sheet per page in `pages/`. Build them in this order, so every link a page makes already has somewhere to go:
`platform`, `fleet`, `work-with-us`, `learn`, `team`, `impact`, `onboarding`, then `home` last. For each:

1. Upload the page's images from `assets/` to **Site Assets** first.
2. Paste the sheet's prompt into Copilot as the sheet says; review the proposal against the sheet's *Sections* table;
   let it build.
3. Do the sheet's *Finish by hand*, publish, and run its *Check*.

The design canvas shows each page as it should look; turn on **Blueprint** in an artboard's Tweaks to see the web
part behind every block.

## 6. The agent

`agent/ask-the-czars.md`: create it, approve it, make it the agent the header opens, and run its check.

## 7. Permissions and sharing

1. Add partners to the site's **Visitors** group (or a security group of them), never as members.
2. Requests: item-level permissions and Visitors' Contribute on that list only (step 2).
3. Onboarding: the page's own permissions, Visitors removed (`pages/onboarding.md`).
4. FleetAgent's lists, when the fleet session puts them on this site: their own permissions, members only.
5. **Settings** > **Site AI**: hide the Copilot button from visitors only if partners should not use the agent.

## What only the tenant can prove

Every row reads *not yet measured* until someone runs it on the tenant. Record each run, with the date and what you
saw, in this-next-please's `docs/windows-verification.md`, in a §Site section beside §Mobile, and change the row here
in the same pull request.

| Row | What | How to see it | Result |
| --- | --- | --- | --- |
| S1 | `ExecuteTemplateScript` applies the twelve scripts with site-owner rights only | step 2, A or B: every list exists | not yet measured |
| S2 | `addSPView` with `viewType2: TILES` and `formatterJSON` makes the gallery views | Tools > Catalog shows cards | not yet measured |
| S3 | `setSPFieldCustomFormatter` formats Status and Maturity | Tools > All Items shows pills | not yet measured |
| S4 | the starter rows land (item types `SP.Data.<List>ListItem`) | Tools has ten rows | not yet measured |
| S5 | Copilot builds each page from its sheet's prompt | each sheet's *Check* | not yet measured |
| S6 | Copilot builds the mega menu from step 4's prompt | the menu matches `site.json` | not yet measured |
| S7 | the site skill loads when someone edits a page | the skill card in Copilot's reply | not yet measured |
| S8 | Ask the Czars answers its check questions with citations | `agent/ask-the-czars.md` §Check | not yet measured |
| S9 | a partner sees only their own requests and no member links | sign in as a Visitors member | not yet measured |
| S10 | every page reads well on a phone, in the browser and the SharePoint app | 390 px wide, both orientations | not yet measured |

## Changing the site later

The repository comes first. Change `lists.json` (then `python site/provision.py docs` and step 2 again), a sheet in
`pages/` (then ask Copilot on that page to apply the change), `site.json`, the skill or the agent; run
`python -m pytest -q`; open a pull request. Running the provisioning again adds columns and views and updates the
formatting; it never deletes a column, a view or a row, so a removal is done by hand on the site and in the spec.
