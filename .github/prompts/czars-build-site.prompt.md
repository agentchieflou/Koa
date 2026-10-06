---
description: Turn the scanned context into the Data Czars site's lists, page prompts and agent files, using the build-czars-site skill.
---
# Build the Data Czars site

Use the `build-czars-site` skill (`.github/skills/build-czars-site/SKILL.md`) from its first step. It checks the
context the scans wrote to `site/local/context/`, asks the operator about every gap it cannot fill, provisions the
lists, and renders the page prompts and the agent files into `site/out/` for the operator to paste into Copilot in
SharePoint and Microsoft 365 Copilot.
