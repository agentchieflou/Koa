---
description: Read the data-czars repository beside Koa and write what the Data Czars site needs about it to site/local/context/data-czars.json. Read-only on data-czars.
---
# Scan data-czars for the site

You are collecting facts for the Data Czars SharePoint site from the `data-czars` repository: the kernel the team
ships for the PAE and the Python package and shell utilities inside it. Koa (this repository) and `data-czars` sit
side by side: from Koa's root it is `../data-czars`. If that folder does not exist, ask the operator for its path and
wait.

## Rules

1. **Read only.** Never edit, build, install, run or commit anything in data-czars, never import its package, and
   never run its shell utilities. The only commands you may run there are
   `git -C ../data-czars remote get-url origin`, `git -C ../data-czars tag --sort=-creatordate` and
   `git -C ../data-czars log -n 30 --format="%h %ad %s" --date=short`.
2. **Never open** `.env*`, anything named `*secret*`, `*credential*`, `*token*`, `*password*`, `*.pem`, `*.key`,
   `*.keytab`, a keyring or any file a keyring or keytab utility writes, data files (`*.csv`, `*.xlsx`, `*.parquet`,
   `*.db`), notebook outputs, or `.agent/out/`. Reading the code of a credential utility is fine; reading what it
   stores is not.
3. **Never copy** a password, token, keyring or keytab path, Kerberos principal, Spark queue name, JDBC URL,
   connection string, database or cluster host, account number, or anything about a customer.
4. Internal URLs and colleagues' names may go into the output file only. It is git-ignored and stays on this laptop.
   Never put them in another file, a commit, or a chat message other than the summary at the end.
5. Plain, short sentences a person new to the kernel understands; no marketing. If the repository does not say it,
   write `""` (or `[]`) and add a line to `gaps` saying what is missing. Never guess, and never work out a number the
   code does not state.
6. **Budget.** Read `PROJECT_CONTEXT.md` first if it exists: it is the repository's own account of itself, and most
   facts below are in it. Then `README*`, `AGENTS.md`, `CHANGELOG*`, `CODEOWNERS`, the packaging file
   (`pyproject.toml`, `setup.cfg`, `setup.py`), the pipeline file, the kernel's definition (`kernel.json` or the
   folder the README names), the names of the top two folder levels, and the titles of `docs/`. Then the module that
   builds Spark sessions, for its named profiles, and at most ten more files the README, the docs or
   `PROJECT_CONTEXT.md` point users to. Stop when you have the facts below.

## Collect

The keys are those of `site/context.example.json`; read it first for the exact shape.

- **`team.mission`**: one sentence on what the kernel and its tooling do for the people who use the PAE.
- **`team.pae`**: what PAE stands for and is, as the repository says it. If it only ever says "PAE", leave `""` and
  add a gap.
- **`team.audience`**: who uses the kernel, in one sentence.
- **`jira`**, from the `AGENTS.md` facts:
  - `url` = `jira_url`; `project` = `jira_project`;
  - `boardUrl` = `<jira_url>/secure/RapidBoard.jspa?rapidView=<jira_board_id>` (Data Center), or the Cloud board
    URL if the Jira is `*.atlassian.net`;
  - `flavour` = `Cloud` for `*.atlassian.net`, otherwise `Data Center`;
  - `components` from `jira_components`; `labels` from `jira_labels` plus `sharepoint-intake`;
  - `issueTypes`: `request`, `question` and `access` are `jira_issue_type`; `issue` is `Bug` only if the repository
    shows the project uses it, otherwise `jira_issue_type` plus a gap.
- **`kernel`**: the kernel as a person meets it in JupyterHub.
  - `name`: as the repository names it, without "the" (pages write "the {name}");
  - `summary`: one sentence: what it is and who it is for;
  - `buildsOn`: one sentence on the kernel it extends, if it extends one;
  - `includes`: the standard packages it adds and the team's own package, as names, at most eight;
  - `connectsTo`: the systems its Spark sessions connect to, as product names (never hosts);
  - `setupSteps`: the documented setup, one short sentence a step, in order, starting from "the access is granted";
    `[]` and a gap if the repository does not document it (the Confluence pages usually do);
  - `firstSession`: the shortest documented code that starts a Spark session in a notebook, copied exactly; `""` and
    a gap if there is none;
  - `docs` and `repo` as `{"url", "desc"}`; `source`, the files you took these from.
- **`products`**: one entry per thing a person uses by name: the kernel itself; each capability of the package a user
  calls directly (for example starting a Spark session, connecting to a source, profiling or comparing data, running
  rules or a pipeline, setting up credentials); and any other tool the repository supports. Never an internal helper
  or a module only other modules call.
  - `name` (what a user would call it; the module in brackets only if users import it by that name), `summary` (one
    or two sentences: what it does for the person using it), `category` (a short noun such as Kernel, Spark,
    Connectors, Data quality, Pipelines, Credentials or Usage);
  - `supportLevel`: Supported, Preview or Deprecated as the repository says; Supported when it says nothing;
  - `status` `Operational`; `version` from the packaging file, the changelog or the newest tag;
  - `howToStart`: one line: the documented import and call, or the documented command, exactly;
  - `docs` and `repo` as `{"url", "desc"}`; `jiraComponent`, the matching name in `jira.components`, else `""`;
  - `featured`: true for at most three, the ones a new user needs first; `source`, the file you took it from.
- **`profiles`**: every named Spark resource profile the session module defines, smallest first.
  - `name` exactly as a user passes it; `executors`, `executorMemory`, `executorCores` and `driverMemory` as the
    code sets them, as text (`"4g"`, `"8"`); `""` for any the profile leaves to the defaults;
  - `kind`: `Standard` for the size ladder, `Specialized` for any other;
  - `useWhen`: what the code's comments or the docs say the profile is for, in one sentence; `""` and a gap if they
    say nothing (the team writes it; never invent one).
- **`access`**: only the entitlements the repository itself names. `name` exactly as written, `why` (one sentence),
  `neededFor` (`Using the kernel` or `Contributing code`), `request` as `{"url", "desc"}` if a request link is given.
  Most of these are on the Confluence pages instead (`site/prompts/confluence-page-facts.md`).
- **`links`**: the repository's browse page (from the git remote), plus every Confluence, Jira, Power BI, Teams or
  SharePoint link the README, the docs or `PROJECT_CONTEXT.md` give to users.
  - `category`: one of Confluence, Bitbucket, Jira, Power BI, Teams, SharePoint, Docs, Other;
  - `shownTo`: `Members` for source code and internal runbooks, `Everyone` otherwise.
- **`releases`**: the last five, newest first, from the changelog or the tags. Each has `product`, `version`,
  `headline` (one line), `kind` (Feature, Fix, Breaking, Security or Notes) and `date` (`YYYY-MM-DD` or `""`).
- **`faq`**: up to eight questions users really hit, with the answer the docs give: errors and their documented fix
  (`topic` `Common errors`; the question is the error as a person sees it, in a few words), access (`Access`), setup
  and profiles (`Getting started`), or a product name. `shownTo` is `Everyone`.

## Write

Write `site/local/context/data-czars.json` with only `team`, `jira`, `kernel`, `products`, `profiles`, `access`,
`links`, `releases`, `faq` and `gaps`, as valid JSON in the shape of `site/context.example.json`. Then run
`python site/provision.py context` and fix whatever it refuses in your file. Never edit a tracked file.

## Finish

Reply in six lines or fewer: the kernel's name, the products and profiles found, the Jira facts found or missing,
how many links and questions, the gaps, and the next step, which is the usage_tool scan (`czars-scan-usage-tool`).
