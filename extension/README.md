# SmartCVapply Chrome Extension

Manifest V3 extension that detects job application forms on any page and pre-fills them with the user's stored profile.

## Stack

- TypeScript (strict) compiled to ESM via esbuild
- Vanilla JS popup (no framework, single HTML file) — epic-design UI in blue
- Shadow DOM banner injected by content script
- React controlled input bypass via `nativeInputValueSetter`
- WebSocket client to backend for live fill progress

## Build

```bash
npm install
npm run build       # produces dist/
npm run watch       # dev with auto-rebuild
npm run typecheck
```

## Load in Chrome

1. Run the backend (see `../backend/README.md`).
2. Open `chrome://extensions`.
3. Enable **Developer mode**.
4. Click **Load unpacked** and select `dist/`.

## Layout

```
extension/
  manifest.json         # Manifest V3
  popup.html            # UI: login, main, fill, settings
  popup.js              # UI logic
  esbuild.config.mjs    # build script
  src/
    background.ts       # service worker: auth, message routing
    content.ts          # form detection, banner, value injection
    content-iframe.ts   # iframe bridge stub
    types.ts            # shared types
  public/icons/         # blue gradient placeholder icons
  dist/                 # build output
```

## UI design

The popup uses the **epic-design** system: 6 depth layers, blue primary palette, GPU-only animations, `prefers-reduced-motion` safe. Three depth-0/1/2 layers create the ambient backdrop; the content sits at depth-3; depth-5 sparkles drift in the foreground.

Color tokens (in `popup.html`):

```css
--blue-500: #3b82f6;  /* primary */
--blue-700: #1d4ed8;  /* hover/active */
--blue-800: #1e40af;  /* deep accents */
```

## Notes for v1.1

- Local engine (Transformers.js) is stubbed — the heuristic resolution and LLM cascade happen in the backend for v1.
- Iframe bridge is a stub.
- Banner click currently tries `chrome.action.openPopup()` which is supported in Chrome 120+.
- The popup expects the backend at `http://localhost:8000`. Change `API_BASE` in `src/background.ts` and `popup.js` for production.
