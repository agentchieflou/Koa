# Step 02: the lists, the bridge library, and the Owners-only lock

**Who:** you write the flow and check its report; the operator imports it, runs it and saves its report.
**Produces:** on `siteUrl`:
- the five lists `FleetAttention`, `FleetApprovals`, `FleetDecisions`, `FleetNotifications` and `FleetHeartbeat`,
  with every column of the contract and an index on `Title` and `Operator`;
- the document library `library` (default `FleetAgent`), with one folder per operator named by their UPN;
- all six locked to the site's **Owners** group: Full Control for that group and nobody else.

You cannot create a SharePoint list yourself, and no MCP server is there to do it. All of this is done by a one-shot
flow, `FleetProvisionLists`, which `build/prepare.py` writes from the pinned contract and the config and the operator
imports and runs. The flow is safe to run more than once:

- it creates a list, column or folder only when it is missing;
- it turns an index on, which changes nothing when it is already on;
- it deletes nothing but permissions: on each list and the library it removes every role assignment except the
  Owners group's.

## 1. Generate the flow

```
python build/prepare.py lists
```

This writes `build/out/FleetProvisionLists.zip`, the package the operator imports, and
`build/out/FleetProvisionLists.json`, the same flow to read. The flow is one Compose (`Spec`) holding the five lists
and the library, then loops that call SharePoint's **Send an HTTP request to SharePoint** (`HttpRequest`), in this
order:

1. the lists and their columns;
2. the indexes;
3. each operator's folder in the library;
4. the lock: break inheritance without copying anyone, grant the Owners group Full Control, remove everyone else,
   and read the assignments back into `Owners_only`;
5. **`Report`**, its last action: every list's columns and lock as SharePoint reads them after the run, and the
   library's folders. This is what you check in section 3.

The column rules come from the contract and `data/README.md`:

| Rule | Detail |
| --- | --- |
| type | every column is text |
| multi-line columns | *Multiple lines of text*, plain (not rich text): `Says`, `ApprovalsJson`, `QuestionsJson`, `PayloadPreview`, `Message`, `AnswersJson` and `Body` |
| internal names | exactly the contract's names (option 25 sets this) |
| skipped columns | `Title` and `Created`, which every list already has (`build/README.md` §The Created column) |
| `Operator` | on every list; with `Title` it identifies a row, so both are indexed |

## 2. Import and run (operator)

The connection must belong to a site **Owner**: breaking a list's inheritance and changing its permissions needs
the Manage Permissions right that Owners have; anyone else gets a 403 at `Break_inheritance`. Send this, with the
path of the zip filled in:

> Please import and run the list flow. About five minutes:
>
> 1. Open https://make.powerautomate.com, check the environment picker (top right) shows **<environment>**, then
>    **My flows** > **Import** > **Import Package (Legacy)**.
> 2. **Upload** `<path>\build\out\FleetProvisionLists.zip`.
> 3. Under **Review package content**, the flow's **Import setup**: **Create as new** (or **Update** if a
>    `FleetProvisionLists` is already there) > **Save**. The SharePoint row's **Import setup**: pick your own
>    SharePoint connection, or **+ Create new** and sign in > **Save**. Then **Import**.
> 4. **Open flow** > **Run** > **Run flow** > **Done**. It takes a minute or two.
> 5. Open the run (it shows under **28-day run history**). Every step should have a green tick. Open the last one,
>    **Report**, select **Show raw outputs**, select all of it, copy it, and save it as
>    `<path>\build\out\lists-report.json` (Notepad is fine). Reply here when it is saved, or paste the error
>    of the first step that is red.

Mark the step `waiting` until they reply.

On a failed run, read the error they paste. The usual causes:

- **403:** the connection's account is not an Owner of the site. Ask the operator to fix that first, then run the
  flow again.
- **400 on `CreateFieldAsXml`:** read the message. A duplicate display name means a column was made by hand
  under another internal name; tell the operator which one.
- **400 on `folders/add`:** an operator's UPN holds a character SharePoint refuses in a folder name. The config
  check refuses most of them; report the one it missed.
- **The import page refuses the package** (row B1 in `build/README.md`): note the exact message, and take the
  fallback below.

If a parameter of the `HttpRequest` action is reported unknown, the operator opens that action in the flow and
reads its parameter names; correct `build/prepare.py`'s `_sp()` (a tracked fix), run `python -m pytest -q`,
regenerate, and have them import again with **Update**.

## 3. Check

```
python build/prepare.py check-lists build/out/lists-report.json
```

**Check:** it says `lists: ready`. Anything else is a line per problem:

- `missing <columns>`: the run stopped part way through that list; ask for the first red step's error.
- `not Owners-only`: someone other than the Owners group can still read that list or the library. Mark the step
  `blocked` and give the list's name.
- `no folder <UPN>`: that operator's bridge folder is missing.

The flow is safe to run again after a fix; ask the operator to run it once more and save the new report over the
old one. When the check passes, the operator may delete `FleetProvisionLists` (**My flows** > **...** > **Delete**);
`prepare.py lists` writes it again whenever it is needed.

Record step 02 as `done`, with the column counts per list:

| List | Columns |
| --- | --- |
| FleetAttention | 27 |
| FleetApprovals | 21 |
| FleetDecisions | 18 |
| FleetNotifications | 12 |
| FleetHeartbeat | 15 |

Each count is in addition to `Title`.

Tell the operator, in one line: the lists and the bridge library are readable by the site's Owners only, so anyone
later made an Owner of the site can read every operator's fleet too.

**Fallback,** only if the import is refused or the HttpRequest action is blocked by the tenant's DLP policy: the
operator creates the lists by hand from `data/FleetAgent.xlsx` following `data/README.md`, the library and folders
in SharePoint, and the permissions under each one's **Settings** > **Permissions for this list** > **Stop inheriting
permissions**, removing everyone but the Owners group. Mark the step `waiting` until they say it is done.
