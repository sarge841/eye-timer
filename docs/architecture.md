# Eye Timer Architecture

> **AI Agents**: For a fast orientation guide, commands, and critical implementation gotchas, start with [`AGENTS.md`](../AGENTS.md).

## 1. Overview
Eye Timer is a single-file Flask application that serves a self-contained front‑end implementing the 20‑20‑20 rule: every configurable X minutes of focus, look 20 feet away for Y seconds. All UI, logic, styles, and scripts are embedded in [`eye-timer.py`](../eye-timer.py) and delivered via one HTML response. No build step or asset pipeline is required.

## 2. High-Level Components
| Layer | Responsibility |
|-------|----------------|
| Flask server | Serves root route (`/`) and favicon (`/favicon.png`); supports `HOST`, `PORT`, and `DEBUG` env overrides. |
| HTML Template | Defines settings modal, fullscreen anti-burn-in backdrop/canvas, timer card, header actions (fullscreen & settings), and controls. |
| Tailwind CDN | Provides utility-first styling (`darkMode: 'class'`, loaded from CDN). |
| Font / Icons | Google Fonts (`Inter`, `JetBrains Mono`) + FontAwesome 6.4.0 for typography and icons. |
| JavaScript App | Implements wall-clock timer state, phase transitions, sound engine, fullscreen API, anti-burn-in screensaver engine, settings persistence, and UI binding. |
| Web Audio API | Generates synthetic notification sounds (`chime`, `digital`, `harp`, `hd2`) with forward/reverse playback, repeat count, and delay. |
| Browser APIs | `Notification`, `localStorage`, Fullscreen API (`requestFullscreen`/`exitFullscreen`), `CanvasRenderingContext2D`, `requestAnimationFrame`, `visibilitychange`. |

## 3. Runtime Flow
1. Flask serves `/` returning the embedded HTML/CSS/JS template.
2. Page loads: `initParticles()` prepares the starfield canvas, `loadSettings()` pulls prior configuration from `localStorage` (and applies theme + dynamic screen state), and `resetTimer()` initializes the focus phase and UI.
3. User starts timer:
   - `startTimeMs` and `endTimeMs` are calculated from `Date.now()` and `remainingMs`.
   - `setInterval(tick, 1000)` reconciles wall-clock time (`endTimeMs - Date.now()`), ensuring background tab throttling never causes timer drift.
   - `rAFLoop()` smoothly updates the progress bar width and steps the anti-burn-in animation when visible.
4. When `remainingMs` reaches `0`, `switchPhase()` toggles between focus and break:
   - Updates durations, status badge, and next-phase preview.
   - Plays synthesized sound via `audio.play(repeatCount, repeatDelay, reverseFlag)`.
   - Sends desktop notification when entering a break (if enabled).
5. User interactions (skip, reset, fullscreen toggle, save settings, theme/notification/reverse/burn-in toggles) mutate `appState` and re-render immediately.

## 4. State Management
`appState` (in JS) holds:
- **Runtime Timer State**: `isRunning`, `isFocus`, `timeLeft`, `totalTime`, `timerId`, `startTimeMs`, `endTimeMs`, `remainingMs`, `finished`.
- **Settings (`appState.settings`)**:
  - `focusTime` (seconds, default `1200`)
  - `breakTime` (seconds, default `20`)
  - `soundType` (`'chime' | 'digital' | 'harp' | 'hd2'`)
  - `volume` (`0-100`, default `50`)
  - `notificationsEnabled` (`boolean`, default `true`)
  - `reverseOnBreakEnd` (`boolean`, default `false`)
  - `repeatCount` (`1-10`, default `1`)
  - `repeatDelay` (`1-10` seconds, default `1`)
  - `burnInEnabled` (`boolean`, default `false`)
  - `burnInMode` (`'drift' | 'bounce' | 'aurora' | 'starfield'`, default `'drift'`)
  - `burnInSpeed` (`10-300`%, default `100`)
  - `burnInColorSpeed` (`10-300`%, default `100`)
  - `burnInParticles` (`10-250`, default `65`)

Persistence: `saveSettings()` writes a JSON blob to `localStorage` under `eyeTimerSettings`; `loadSettings()` reads, validates, and applies it on startup.

UI references are cached in `els` for efficient DOM access; no frontend framework (React/Vue) is used.

## 5. Sound Engine
`SoundEngine` encapsulates Web Audio usage:
- Creates a single `AudioContext`.
- `play(repeatCount, repeatDelay, reverse = false)` recursively schedules synthesized tones based on the selected profile:
  - `chime`: Dual sine tones (660Hz → 880Hz, or 880Hz → 660Hz in reverse).
  - `digital`: Double square-wave beep (800Hz).
  - `harp`: Four-note triangle-wave arpeggio (ascending normally, descending in reverse).
  - `hd2`: Low 55Hz triangle drone buildup followed by a melodic triangle sequence.
- Each note instantiates an oscillator with an attack/exponential-decay gain envelope.

## 6. Header Actions & Fullscreen Support
- The card header includes `#toggle-fullscreen` immediately next to `#open-settings`.
- `toggleFullscreen()` invokes `document.documentElement.requestFullscreen()` or `document.exitFullscreen()` (with `webkit` fallbacks).
- `fullscreenchange` and `webkitfullscreenchange` listeners invoke `updateFullscreenUI()` to toggle `#fullscreen-icon` between `fa-expand` and `fa-compress`, keeping the button icon accurate even when exiting fullscreen via `Esc`.

## 7. Dynamic Screen / Anti-Burn-In Engine
To prevent OLED burn-in and LCD image retention during long focus sessions without distracting timer movement:
- **Settings Controls**: Users can toggle `#burn-in-toggle` (`Dynamic Screen (Anti-Burn-In)`) and choose a background style from `#burn-in-mode` (`Dynamic Screen Style`).
- **Stationary, Simpler Semi-Transparent Interface**:
  - The timer card (`#app` / `#main-card`) remains stationary in the center of the viewport.
  - In its dimmed state (`body.burn-in-active.burn-in-idle`), `#main-card` becomes a subtle, semi-transparent glass window so the moving background behind it shines through, surrounding menu chrome (`.burn-in-dimmable`: header bar, control buttons, footer reminder) fades away (`opacity: 0; pointer-events: none;`), and the `XX:XX` countdown (`#timer-display`) stays visible in a softer, lower-contrast color that remains easy to read.
  - **Click Anywhere to Wake (15s Inactivity Timeout)**: Clicking anywhere on the screen (outside `#settings-modal`) triggers `wakeBurnInMenu()`, making the entire timer menu clearly visible (`opacity: 1`) for 15 seconds (`BURN_IN_IDLE_TIMEOUT_MS = 15000`) before smoothly dimming away again.
  - **Settings Modal**: `#settings-modal` displays with normal full visibility whenever open.
- **Four Background Styles**:
  1. **Ambient Orbs (`drift`)**: Moves two blurred ambient color orbs (`#burn-in-drift-orb`, `#burn-in-drift-orb-secondary`) along smooth 2D Lissajous curves behind the semi-transparent timer while cycling hues.
  2. **Color Bounce (`bounce`)**: Moves a soft glowing spotlight orb (`#burn-in-bounce-orb`) diagonally across the viewport, bouncing off edges and cycling through theme-aware color palettes (`BOUNCE_PALETTES.dark` and `BOUNCE_PALETTES.light`).
  3. **Ambient Aurora (`aurora`)**: Displays animated, softly blurred aurora borealis layers (`#burn-in-aurora-layer`) flowing behind the semi-transparent timer card.
  4. **Cosmic Drift (`starfield`)**: Animates 65 twinkling/drifting particles on `#burn-in-canvas` across the viewport and behind the semi-transparent timer card.
- **Theme Awareness**: Every mode respects Dark Mode (`html.dark`) and Light Mode (`html:not(.dark)`). Dark mode uses OLED-safe deep backgrounds (`#020617`) and soft luminous accents; light mode uses soft daylight backgrounds (`#f1f5f9`) and balanced slate/pastel accents.

## 8. Settings Modal & Independent Toggles
- Modal collects numeric inputs (focus minutes, break seconds, repeat count, repeat delay), sound selection + test button, volume slider, theme toggle, notification toggle, reverse-sound toggle, and dynamic screen anti-burn-in toggle + mode selector.
- Toggle switches (`#notification-toggle`, `#reverse-toggle`, `#burn-in-toggle`) use `updateToggleKnobUI()` to manage knob position and background classes independently of the dark mode class.

## 9. Rendering & Feedback
- Timer updates once per second via `tick()` (wall-clock delta) and every animation frame via `rAFLoop()`.
- Dynamic text rewrites: `document.title`, header `h1`, and bottom reminder line reflect custom focus/break durations.
- Phase badges use distinct color sets for visual separation (`brand` blue for Focus, `emerald` green for Break).

## 10. Security & Performance Notes
- No user-supplied HTML is rendered (minimal XSS surface).
- `localStorage` stores only client-side UI preferences.
- Flask debug mode is disabled by default (`DEBUG = False`).
- Anti-burn-in animations use GPU-composited `transform: translate3d(...)` and pause automatically when `document.hidden` is true.

## 11. Quick Data Flow Summary
```
User Action --> DOM Event Listener --> Mutate appState.settings/state --> saveSettings()/resetTimer()/switchPhase()/applyBurnInState()
                                     |                                      |
                                     v                                      v
                              updateUI() / rAFLoop() ------> DOM updates (title, text, progress, 3D transform, canvas)
                                            \-> audio.play(repeatCount, repeatDelay, reverseFlag)
                                            \-> Notification (if enabled & break phase)
```

## 12. Deployment & Testing
Run locally with `uv`:
```bash
uv run eye-timer.py
```
Run the unit and Flask frontend integration test suite:
```bash
uv run tests/test_eye_timer.py
uv run python -m unittest discover -v
```
