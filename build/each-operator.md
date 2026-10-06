# Connecting your laptop to FleetAgent

For each operator, once, after the build. It takes about five minutes. The build made a folder named by your UPN in
the site's `FleetAgent` library, readable by the site's Owners only. Your laptop's bridge writes into that folder,
and your phone's prompts and decisions arrive there. Nobody else's laptop reads it.

You need to be an Owner of the site. If the library doesn't show your folder, ask whoever ran the build to add your
UPN to `operators` and run step 02 again.

## 1. Sync your folder (shortcut, not Sync)

1. In the browser, open the site, then **Site contents** > **FleetAgent** (the library).
2. Point at **your** folder (your UPN), open **...**, and choose **Add shortcut to My files** (or **Add shortcut to
   OneDrive**).
   - Use the shortcut, not the library's **Sync** button. Microsoft recommends shortcuts for this, and OneDrive
     refuses to do both for one library.
   - Add only your own folder. Your laptop never needs the others'.
3. On the laptop, the folder appears under your OneDrive as `%OneDriveCommercial%\<your UPN>`. Right-click it and
   choose **Always keep on this device**. The bridge's doctor fails an online-only `inbox`.

## 2. Point the bridge at it

```
ad-setup --patch fleet.mobile
```

Answer the five questions:

| Question | Answer |
| --- | --- |
| enabled | yes |
| folder | `%OneDriveCommercial%/<your UPN>` |
| operator | your UPN |
| expire_s | 900 |
| notify | yes |

Then:

```
ad-fleet mobile init      # outbox/, inbox/, processed/, rejected/ and pairing.json inside your folder
ad-doctor                 # fleet/mobile reads ok; a fail names its fix
ad-fleet serve            # the bridge runs as its thread; or `ad-fleet mobile watch` with no desk
```

Within 300 seconds a heartbeat file appears in `<your folder>\outbox\heartbeat\`, and the site's `FleetAgent`
library shows it under your folder.

## 3. The phone

Install **Power Apps** from the store, sign in with the same account, and open **FleetAgent** once. Pushes reach
only someone who has opened the app in the last 30 days.

**Check, in the app:**
- **Home** says *Showing my fleet* and lists your repositories.
- No banner. The heartbeat row is yours, and the laptop's operator is you.
- *Show the team's* lists everyone's, read-only. Approve, Deny and Reply work only on your own rows, and on
  anyone else's the app says whose they are.

Then try the first prompt round trip in [TESTING.md](../TESTING.md) §3.
