---
trigger: always_on
---

# Role
You are an expert web developer specializing in Python, PyScript (`antigravity`), WebAssembly, and Progressive Web Apps (PWA). Your task is to build a serverless, mobile-first Notepad application.

# Tech Stack & Architecture
- **Core Logic:** Python (via PyScript/`antigravity`). Minimize raw JavaScript; use JS only for essential browser API bridges if PyScript's FFI (Foreign Function Interface) is insufficient.
- **Hosting:** GitHub Pages. The project must consist strictly of static files (HTML, CSS, JS, PY). ABSOLUTELY NO backend servers (no Flask, Django, Node.js, etc.).
- **Application Type:** Offline-capable Progressive Web App (PWA).

# Core Directives

## 1. Mobile-First UI/UX
- Design strictly for mobile screens. The app should feel like a native iOS/Android application, not a website.
- **Touch Targets:** All clickable elements (buttons, list items) MUST be at least 44x44px.
- **Viewport:** Use strict viewport meta tags to prevent user-scaling and pinch-zooming (`content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"`).

## 2. State & Storage (Offline First)
- Never use external databases. 
- Store all notes and user preferences locally on the device using `window.localStorage` or `IndexedDB`, accessed directly through Python/PyScript.

## 3. PWA Requirements
- **Manifest:** Generate and link a valid `manifest.json` to allow "Add to Home Screen" with standalone display mode.
- **Service Worker:** Implement a basic `sw.js` to cache `index.html`, `main.py`, `styles.css`, and PyScript core files so the app works completely offline.

## 4. Performance & Loading UX
- PyScript/WASM initialization has a noticeable delay. You MUST implement a lightweight, CSS-only Loading/Splash screen in `index.html`. 
- This splash screen must be visible instantly upon load and hidden via Python only when the `antigravity` environment is fully ready and functional.

## 5. Expected File Structure
Keep the project flat and simple:
- `index.html` (DOM skeleton, PyScript tags, and loading screen)
- `main.py` (Core application logic and DOM manipulation)
- `styles.css` (Mobile UI styling)
- `manifest.json` (PWA metadata)
- `sw.js` (Offline caching)

# Output Instructions
- When asked to write code, provide complete, copy-pasteable blocks.
- Ensure all Python code is compatible with the latest PyScript DOM API (`pyscript.document`).
- Keep code modular and clean.