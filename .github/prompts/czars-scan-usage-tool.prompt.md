---
description: Read the usage_tool repository beside Koa and write what the Data Czars site needs about it to site/local/context/usage_tool.json. Read-only on usage_tool.
---
# Scan usage_tool for the site

You are collecting facts for the Data Czars SharePoint site from the `usage_tool` repository, which produces the usage
reports the site publishes for its members to download. From Koa's root it is `../usage_tool`. If that folder does
not exist, ask the operator for its path and wait.

## Rules

1. **Read only.** Never edit, build, install, run or commit anything in usage_tool, and never run the tool itself.
   The only commands you may run there are `git -C ../usage_tool remote get-url origin`,
   `git -C ../usage_tool tag --sort=-creatordate` and
   `git -C ../usage_tool log -n 30 --format="%h %ad %s" --date=short`.
2. **Never open** `.env*`, anything named `*secret*`, `*credential*`, `*token*`, `*password*`, `*.pem`, `*.key`, any
   report or data file it has produced (`*.csv`, `*.xlsx`, `*.parquet`, `*.db`, output folders), notebook outputs,
   or `.agent/out/`. Learn what a report contains from the code and the docs, never from a real report.
3. **Never copy** a password, token, connection string, database host, user name from activity data, or anything
   about a customer.
4. Internal URLs may go into the output file only. It is git-ignored and stays on this laptop.
5. Plain, short sentences; if the repository does not say it, write `""` and add a line to `gaps`. Never guess.
6. **Budget.** Read `README*`, `AGENTS.md`, `CHANGELOG*`, the packaging file, the entry point the README names, the
   module that writes the report files, the scheduler or pipeline file, and the titles of `docs/`. At most twelve
   files beyond those.

## Collect

The keys are those of `site/context.example.json`; read it first for the exact shape.

- **`usageTool`**:
  - `name`: what the team calls it. `summary`: one or two sentences on what it measures and for whom.
  - `howItWorks`: three to five short steps, from where it reads to what it writes.
  - `reportTypes`: one per kind of report it produces, each with `name` (the words a reader would use, not the file
    prefix), `description` (what the reader finds in it), `period` (Daily, Weekly, Monthly, Quarterly or Ad hoc) and
    `format` (the file extension).
  - `schedule`: when it runs, as the code or the pipeline says.
  - `fileNaming`: the pattern of the files it writes, with placeholders in angle brackets.
  - `outputLocation`: where the files go today, in words (a laptop folder, a share, a database), with no host names.
  - `repo` as `{"url", "desc"}`; `source`, the files you took this from.
- **`products`**: one entry for the usage tool itself, in the same shape as `site/context.example.json`'s products,
  with `category` `Reporting`. Leave `jiraComponent` `""` unless the repository names one.
- **`links`**: the repository's browse page (category Bitbucket, shownTo Members), and every Confluence, Jira, Power BI
  or SharePoint link its docs give to report readers.
- **`releases`**: the last three, newest first, with `product` set to the usage tool's `name`.
- **`faq`**: up to four questions report readers ask (what a column means, when the month's reports arrive, why a
  number moved), each with the answer the docs give. `topic` is the usage tool's `name`.

## Write

Write `site/local/context/usage_tool.json` with only `usageTool`, `products`, `links`, `releases`, `faq` and `gaps`,
as valid JSON. Then run `python site/provision.py context` and fix whatever it refuses in your file. Never edit a
tracked file.

## Finish

Reply in five lines or fewer: the report types found and their period, the schedule, the gaps, and the next step,
which is the fleet scan (`czars-scan-fleet`).
