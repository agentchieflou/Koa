# Step 04: the blank app (the operator's clicks)

**Who:** the operator, with you reading each click to them. The Canvas Authoring MCP server can only write into an
app that already exists, is saved, and has coauthoring on. Display settings and data sources are not in the app's
YAML at all ([Learn](https://learn.microsoft.com/power-apps/maker/canvas-apps/create-canvas-external-tools)).
**Produces:** `studioUrl` and `appId` in the config, and the canvas MCP server connected to the app.

## 1. Tell the operator

Send this, with the environment's display name from the state file filled in:

> Please create the app shell. About three minutes:
>
> 1. Open https://make.powerapps.com and check that the environment picker (top right) shows **<environment>**.
> 2. **+ Create** > **Blank app** > **Blank canvas app** > App name `FleetAgent`, Format **Tablet** > **Create**.
>    Tablet is right for phones too: the app is responsive.
> 3. Open **Settings** (the gear, or **...** > **Settings**) and set:
>    - **Updates** > **New**: **Modern controls and themes** On, and **Enhanced component properties** On if it is
>      listed (the header component's Back, Refresh and Settings events need it).
>    - **Updates** > **Coauthoring**: On. If Studio asks, save the app first and come back.
>    - **Display**: **Scale to fit** Off, **Lock aspect ratio** Off, **Lock orientation** Off, then **Apply**.
>    - **General**: leave the data row limit at 500.
> 4. Save the app (Ctrl+S) under the name `FleetAgent`.
> 5. Copy the address from the browser's address bar (it contains `app-id=`), paste it here, and **leave that tab
>    open** for the rest of the build.

Mark the step `waiting` until they paste the URL.

## 2. Read the URL

The URL looks like `https://make.powerapps.com/e/<ENV_ID>/canvas/?action=edit&app-id=%2Fproviders%2FMicrosoft.PowerApps%2Fapps%2F<APP_ID>`.

1. URL-decode `app-id` and take the last path segment: that is `appId`.
2. Take `<ENV_ID>`, the segment after `/e/`. It must be the environment from step 01. If it is not, the app is
   in the wrong environment; ask the operator to recreate it in the right one.
3. Write `studioUrl` and `appId` into `build/fleet.config.json`.

## 3. Connect the canvas MCP server

Follow the canvas-apps plugin's `configure-canvas-mcp` skill:

1. Call `connect` with `environment_id` (`ENV_ID`), `app_id` (`APP_ID`) and `environment_category`. The category
   is `prod` for `make.powerapps.com`; the skill's table has the others.
2. If a sign-in window opens, the operator completes it.

**Check:** `list_controls` returns the control list, and `list_data_sources` answers (empty is fine at this
point). Mark step 04 `done`.
