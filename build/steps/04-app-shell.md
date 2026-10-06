# Step 04: the blank app (the operator's clicks)

**Who:** the operator, with you reading each click to them. Display settings and data sources are not in the app's
YAML at all, so they are set in Studio; the screens arrive in step 06 by pasting.
**Produces:** `environment`, `studioUrl` and `appId` in the config.

## 1. Tell the operator

Send this, with the environment's name from the state file filled in:

> Please create the app shell. About three minutes:
>
> 1. Open https://make.powerapps.com and check that the environment picker (top right) shows **<environment>**.
> 2. **+ Create** > **Blank app** > **Blank canvas app** > App name `FleetAgent`, Format **Tablet** > **Create**.
>    Tablet is right for phones too: the app is responsive.
> 3. Open **Settings** (the gear, or **...** > **Settings**) and set:
>    - **Updates** > **New**: **Modern controls and themes** On, and **Enhanced component properties** On if it is
>      listed (the header component's Back, Refresh and Settings events need it).
>    - **Display**: **Scale to fit** Off, **Lock aspect ratio** Off, **Lock orientation** Off, then **Apply**.
>    - **General**: leave the data row limit at 500.
> 4. Save the app (Ctrl+S) under the name `FleetAgent`.
> 5. Right-click **Screen1** in the tree view and check the menu has **View code** and **Paste code**. If it does
>    not, look under **Settings** > **Updates** for the Power Fx formula bar or code view and turn it on.
> 6. Copy the address from the browser's address bar (it contains `app-id=`), paste it here, and **leave that tab
>    open** for the rest of the build.

Mark the step `waiting` until they paste the URL.

## 2. Read the URL

The URL looks like `https://make.powerapps.com/e/<ENV_ID>/canvas/?action=edit&app-id=%2Fproviders%2FMicrosoft.PowerApps%2Fapps%2F<APP_ID>`.

1. URL-decode `app-id` and take the last path segment: that is `appId`.
2. Take `<ENV_ID>`, the segment after `/e/`: that is `environment`.
3. Write `environment`, `studioUrl` and `appId` into `build/fleet.config.json`, and run
   `python build/prepare.py check`.

**Check:** `flows: ready`. If the operator says the environment picker showed another environment than the one in
step 01, the app is in the wrong place; ask them to recreate it in the right one. Mark step 04 `done`.
