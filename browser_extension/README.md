# Crane browser extension

Chrome MV3 client for the Crane OSINT platform. Volunteers capture evidence
from the page they're investigating without leaving the browser.

## Three surfaces

- **Side panel** — Capture form (with full-page screenshot), project picker, "Suggest next searches" list.
- **Content script** — Compact toast on pages already in the user's project ("Already in Crane · REC-042").
- **Toolbar icon badge** — Grey (not connected), green (connected, fresh), amber (duplicate), red (auth/network error).

## Install for testers (load unpacked)

The extension is currently distributed as an unpacked Chrome extension. It is
not yet on the Chrome Web Store.

1. Download or clone the Crane repo and run `npm install` + `npm run build`
   inside `browser_extension/`. The build output goes to `browser_extension/dist/`.
2. Open `chrome://extensions` in Chrome 114+.
3. Toggle **Developer mode** on (top right).
4. Click **Load unpacked** and select the `browser_extension/` directory
   (the one containing `manifest.json`, not the `dist/` subdirectory — the
   manifest references `dist/*` itself).
5. Pin the Crane icon from the puzzle-piece menu so it's visible.
6. Click the Crane icon → side panel opens → click **Connect**. A login tab
   opens; sign in with your Crane account; the panel updates with your
   project list automatically.

The first install asks for the **"Read and change all your data on websites
you visit"** permission. This is required by the passive duplicate-badge
content script — it has to know what URL each tab is on. The extension
sends only the page URL to your Crane backend, never page contents.

## Pointing at a different Crane host

The Connect screen has a **Crane base URL** input pre-filled with
`http://localhost:8000`. Type the URL of your Crane install (no trailing
slash, must start with `http://` or `https://`) and click **Connect** — the
URL is persisted and reused on subsequent reloads. Click **Disconnect** to
return to the Connect screen and re-pick the host.

The default is set in `src/background/sw.ts` (`DEFAULT_BASE_URL`); change
it there if you want a different prefilled value for fresh installs.

## Development

```bash
cd browser_extension
npm install            # one-time
npm run build          # one-shot production build → dist/
npm run dev            # watch mode; rebuilds on changes
npm run typecheck      # tsc --noEmit
```

After `npm run build` runs once, reload the extension from
`chrome://extensions` (the circular-arrow icon on the Crane card) to pick
up changes. The side panel and content script auto-reload; the service
worker restarts on next event.

## Layout

```
browser_extension/
├── manifest.json              # MV3 manifest
├── package.json               # devDeps only — no runtime npm packages ship
├── tsconfig.json              # strict TS
├── build.mjs                  # esbuild driver (3 entry points)
├── icons/                     # 16/48/128 PNG of the Crane mark
├── src/
│   ├── shared/
│   │   ├── types.ts           # API DTOs + message protocol
│   │   ├── normalize-url.ts   # mirror of apps/incidents/utils.normalize_url
│   │   ├── storage.ts         # typed chrome.storage.local wrappers
│   │   └── api-client.ts      # fetch() against /api/v1/
│   ├── background/sw.ts       # service worker: dispatch + auth + badge
│   ├── content/index.ts       # duplicate-toast content script
│   └── sidepanel/
│       ├── index.html
│       ├── styles.css
│       ├── state.ts
│       ├── render.ts          # vanilla DOM tree builder, no innerHTML
│       └── index.ts           # entry point + dispatch table
└── dist/                      # build output (gitignored)
```

## Message protocol

All messages go through `chrome.runtime.sendMessage` and are dispatched by
the background SW's table in `src/background/sw.ts`. Request/response shapes
are discriminated unions in `src/shared/types.ts`.

| Type             | Sender → Receiver        | Purpose                             |
| ---------------- | ------------------------ | ----------------------------------- |
| `INITIATE_AUTH`  | side panel → background  | Run `chrome.identity.launchWebAuthFlow` and persist the token |
| `CLEAR_AUTH`     | side panel → background  | Drop the token                      |
| `GET_AUTH_STATE` | side panel → background  | Read persisted auth                 |
| `GET_PROJECTS`   | side panel → background  | Fetch `/api/v1/projects`            |
| `CHECK_URL`      | side panel + content → background | Fetch `/api/v1/incidents/check` (with 5-min cache) |
| `CAPTURE`        | side panel → background  | Submit `/api/v1/incidents/capture`  |
| `GET_SUGGESTIONS`| side panel → background  | Fetch `/api/v1/coverage/suggest`    |
| `TAKE_SCREENSHOT`| side panel → background  | `chrome.tabs.captureVisibleTab`     |
| `PAGE_URL_CHANGED` | background → content   | SPA history-state push fired        |
| `AUTH_UPDATED` / `AUTH_CLEARED` | background → side panel | Broadcast auth state changes |
