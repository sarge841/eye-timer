# AI Agent Orientation Guide (`AGENTS.md`)

Welcome! This document is designed to get AI coding agents (Antigravity, Claude Code, Cursor, GitHub Copilot, Windsurf, etc.) oriented and productive in this repository immediately.

---

## 1. Project Summary & Core Philosophy
- **What it is**: **Eye Timer** is a lightweight web application implementing the **20-20-20 rule** (every 20 minutes of focus, look 20 feet away for 20 seconds, with customizable durations).
- **Single-File Architecture**: The entire application—Flask server, HTML markup, CSS styles, and vanilla JavaScript—lives inside [`eye-timer.py`](eye-timer.py) via the `HTML_TEMPLATE` string.
- **Zero Build Step**: Styling uses the Tailwind CSS CDN (`darkMode: 'class'`), icons use FontAwesome 6.4.0 CDN, and audio uses the browser's native **Web Audio API** (synthesized tones, zero external audio assets).
- **Rule of Thumb**: Keep the single-file simplicity intact unless the user explicitly asks to split static assets into separate files.

---

## 2. Repository Layout
| Path | Purpose |
|------|---------|
| [`eye-timer.py`](eye-timer.py) | Main executable Flask app containing backend routes (`/`, `/favicon.png`) and the embedded `HTML_TEMPLATE` frontend. |
| [`tests/test_eye_timer.py`](tests/test_eye_timer.py) | Unit tests for timer/settings state (`TestEyeTimer`) and Flask integration/DOM tests (`TestFlaskAppFrontend`). |
| [`tests/__init__.py`](tests/__init__.py) | Package marker required so `python -m unittest discover -v` (used in CI) discovers tests in `tests/`. |
| [`docs/architecture.md`](docs/architecture.md) | Detailed technical architecture, runtime flow, state model, and subsystem breakdown. |
| [`README.md`](README.md) | User-facing overview, features, setup, and usage instructions. |
| [`pyproject.toml`](pyproject.toml) / [`uv.lock`](uv.lock) | Python project metadata and locked dependencies (`flask`) managed by `uv`. |
| [`Dockerfile`](Dockerfile) | Container build definition based on `ghcr.io/astral-sh/uv:debian`. |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions workflow running unit tests and building/pushing multi-arch Docker images (`linux/amd64`, `linux/arm64`) to GHCR. |

---

## 3. Essential Commands
This repository uses [`uv`](https://docs.astral.sh/uv/) for dependency management and script execution.

```bash
# Run the web app locally (serves on http://0.0.0.0:5000 by default)
uv run eye-timer.py

# Run the test suite directly via uv
uv run tests/test_eye_timer.py

# Run the test suite via unittest discovery (matches GitHub Actions CI)
uv run python -m unittest discover -v
```

### Environment Variables
- `HOST`: Bind address (default: `0.0.0.0`)
- `PORT`: Bind port (default: `5000`)
- `DEBUG`: Flask debug mode (`1`, `true`, `yes` to enable; default: `False`)

---

## 4. Key Subsystems in `eye-timer.py`

### A. Timer & Wall-Clock Synchronization
- State lives in `appState`:
  - `isRunning`, `isFocus`, `timeLeft`, `totalTime`, `timerId`
  - `startTimeMs`, `endTimeMs`, `remainingMs`, `finished`
- **Why wall-clock timestamps?** Browsers throttle `setInterval` in background tabs. `tick()` calculates remaining time via `appState.endTimeMs - Date.now()` and catches up missed phases in a `while` loop.
- **Important invariant**: The `visibilitychange` event listener and `rAFLoop()` only advance/update the timer when `appState.isRunning === true`. Pausing snapshots `remainingMs` and clears `endTimeMs`.

### B. Web Audio Synthesizer (`SoundEngine`)
- Uses `window.AudioContext` to synthesize 4 notification profiles without external audio files:
  - `chime` (sine wave two-tone chime)
  - `digital` (square wave double beep)
  - `harp` (triangle wave arpeggio)
  - `hd2` (low triangle buildup sequence)
- **Reverse on Break End (`reverseOnBreakEnd`)**: When transitioning from Break (`isFocus === false`) back into Focus (`nextIsFocus === true`) and `reverseOnBreakEnd` is enabled, `audio.play(repeatCount, repeatDelay, true)` plays the inverted note sequence.

### C. Header Controls: Fullscreen & Settings
- Located in the header of `#main-card`:
  - `#toggle-fullscreen` (with `<i id="fullscreen-icon" class="fa-solid fa-expand"></i>`) sits immediately to the left of `#open-settings` (`fa-gear`).
- `toggleFullscreen()` wraps the Fullscreen API (`requestFullscreen` / `exitFullscreen` with `webkit` fallbacks), and `fullscreenchange` listeners keep the icon (`fa-expand` vs `fa-compress`) in sync even when the user exits fullscreen with the `Esc` key.

### D. Dynamic Screen / Anti-Burn-In Engine
- Designed to prevent OLED/monitor burn-in and image retention while keeping the countdown, status badge, progress bar, and controls live.
- Controlled by `appState.settings.burnInEnabled` (`#burn-in-toggle`) and `appState.settings.burnInMode` (`#burn-in-mode`).
- **4 Supported Modes** (`VALID_BURN_IN_MODES`):
  1. `drift` (**Gentle Orbit / Pixel Drift**): Moves `#app` along a continuous 2D Lissajous curve across the viewport with a softly shifting ambient glow orb (`#burn-in-drift-orb`).
  2. `bounce` (**DVD Bounce / Color Shift**): Bounces `#app` diagonally off viewport edges and cycles through theme-aware accent palettes (`BOUNCE_PALETTES.dark` and `BOUNCE_PALETTES.light`) on each wall collision.
  3. `aurora` (**Ambient Aurora / Waves & Wander**): Renders animated blurred aurora blobs (`#burn-in-aurora-layer`) behind a translucent glassmorphic wandering timer HUD.
  4. `starfield` (**Cosmic Drift / Particles & Wander**): Renders drifting/twinkling particles on `#burn-in-canvas` (`renderStarfield()`) with a translucent wandering timer HUD.
- **Dark Mode & Light Mode Support**:
  - All 4 modes check `isDarkMode()` (`document.documentElement.classList.contains('dark')`) and use Tailwind `dark:` classes plus CSS rules (`html.dark body.burn-in-active` vs `html:not(.dark) body.burn-in-active`).
- **Interaction & Layout Gotchas**:
  - **Pause on Hover / Modal**: Card movement pauses automatically when the user hovers over `#app` (`burnInState.isHoveringCard`) or when `#settings-modal` is open, so buttons are never a moving target.
  - **Idle Chrome Dimming**: Elements with `.burn-in-dimmable` (header, controls panel, footer text) dim to low opacity after 3 seconds of mouse inactivity (`body.burn-in-idle`) and restore to 100% opacity immediately on mouse movement or hover.
  - **CSS Containing Block Rule**: `#settings-modal` is intentionally placed **outside** `#app` as a direct child of `<body>`. Because `#app` uses `transform: translate3d(...)` during anti-burn-in movement, placing a `position: fixed` modal inside `#app` would trap the modal inside the transformed card's coordinate space. Keep `#settings-modal` outside `#app`!

### E. Persistence (`localStorage`)
- Settings are stored as JSON under the `localStorage` key `'eyeTimerSettings'`.
- Saved keys: `focus`, `break`, `sound`, `volume`, `reverse`, `repeatCount`, `repeatDelay`, `theme`, `notificationsEnabled`, `burnInEnabled`, `burnInMode`.

---

## 5. Checklist When Making Changes
1. **Update `eye-timer.py`**: Keep HTML, CSS, and JS cohesive and self-contained.
2. **Update `tests/test_eye_timer.py`**: Add/update unit and Flask frontend tests for any new settings, DOM elements, or routes.
3. **Run Tests**: Verify both `uv run tests/test_eye_timer.py` and `uv run python -m unittest discover -v` pass.
4. **Keep Documentation Current**: Update [`README.md`](README.md), [`docs/architecture.md`](docs/architecture.md), and this [`AGENTS.md`](AGENTS.md) file whenever features, settings, or architectural patterns change.
