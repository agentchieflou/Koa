---
description: Read the data-czars repository beside Koa and write what the Data Czars site needs about it to site/local/context/data-czars.json. Read-only on data-czars.
---
# Scan data-czars for the site

You are collecting facts for the Data Czars SharePoint site from the `data-czars` repository, which holds the tooling
the team supports in the PAE. Koa (this repository) and `data-czars` sit side by side: from Koa's root it is
`../data-czars`. If that folder does not exist, ask the operator for its path and wait.

## Rules

1. **Read only.** Never edit, build, install, run or commit anything in data-czars. The only commands you may run
   there are `git -C ../data-czars remote get-url origin`, `git -C ../data-czars tag --sort=-creatordate` and
   `git -C ../data-czars log -n 30 --format="%h %ad %s" --date=short`.
2. **Never open** `.env*`, anything named `*secret*`, `*credential*`, `*token*`, `*password*`, `*.pem`, `*.key`,
   data files (`*.csv`, `*.xlsx`, `*.parquet`, `*.db`), notebook outputs, or `.agent/out/`.
3. **Never copy** a password, token, connection string, database host, account number, or anything about a customer.
4. Internal URLs and colleagues' names may go into the output file only. It is git-ignored and stays on this laptop.
   Never put them in another file, a commit, or a chat message other than the summary at the end.
5. Plain, short sentences a partner team understands; no marketing. If the repository does not say it, write `""`
   and add a line to `gaps` saying what is missing. Never guess.
6. **Budget.** Read `README*`, `AGENTS.md`, `CHANGELOG*`, `CODEOWNERS`, the packaging file (`pyproject.toml`,
   `setup.cfg`, `package.json`), the pipeline file, the names of the top two folder levels, the titles of `docs/`,
   then at most ten more files the README or docs point users to. Stop when you have the facts below.

## Collect

The keys are those of `site/context.example.json`; read it first for the exact shape.

- **`team.mission`**: one sentence on what the tooling does for the people who use the PAE.
- **`team.pae`**: what PAE stands for and is, as the repository says it. If it only ever says "PAE", leave `""` and
  add a gap.
- **`team.audience`**: who uses the tooling, in one sentence.
- **`jira`**, from the `AGENTS.md` facts:
  - `url` = `jira_url`; `project` = `jira_project`;
  - `boardUrl` = `<jira_url>/secure/RapidBoard.jspa?rapidView=<jira_board_id>` (Data Center), or the Cloud board
    URL if the Jira is `*.atlassian.net`;
  - `flavour` = `Cloud` for `*.atlassian.net`, otherwise `Data Center`;
  - `components` from `jira_components`; `labels` from `jira_labels` plus `sharepoint-intake`;
  - `issueTypes`: `request`, `question` and `access` are `jira_issue_type`; `issue` is `Bug` only if the repository
    shows the project uses it, otherwise `jira_issue_type` plus a gap.
- **`products`**: one entry per tool or product the repository supports for users of the PAE, not per module.
  - `name`, `summary` (one or two sentences: what it does for the person using it), `category` (a short noun such as
    Monitoring, Governance, Reporting, Automation or Data);
  - `supportLevel`: Supported, Preview or Deprecated as the repository says; Supported when it says nothing;
  - `status` `Operational`; `version` from the packaging file, the changelog or the newest tag;
  - `howToStart`: one sentence or one command, exactly as documented;
  - `docs` and `repo` as `{"url", "desc"}`; `jiraComponent`, the matching name in `jira.components`;
  - `featured`: true for at most three, the ones users need most; `source`, the file you took it from.
- **`links`**: the repository's browse page (from the git remote), plus every Confluence, Jira, Power BI, Teams or
  SharePoint link the README or docs give to users.
  - `category`: one of Confluence, Bitbucket, Jira, Power BI, Teams, SharePoint, Docs, Other;
  - `shownTo`: `Members` for source code and internal runbooks, `Everyone` otherwise.
- **`releases`**: the last five, newest first, from the changelog or the tags. Each has `product`, `version`,
  `headline` (one line), `kind` (Feature, Fix, Breaking, Security or Notes) and `date` (`YYYY-MM-DD` or `""`).
- **`faq`**: up to six questions users really hit, from troubleshooting or known-issues sections, each with the
  answer the docs give. `topic` is a product name or `Getting help`; `shownTo` is `Everyone`.

## Write

Write `site/local/context/data-czars.json` with only `team`, `jira`, `products`, `links`, `releases`, `faq` and
`gaps`, as valid JSON in the shape of `site/context.example.json`. Then run `python site/provision.py context` and
fix whatever it refuses in your file. Never edit a tracked file.

## Finish

Reply in five lines or fewer: the products found, the Jira facts found or missing, how many links, the gaps, and
the next step, which is the usage_tool scan (`czars-scan-usage-tool`).
