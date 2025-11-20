# Eye Timer Architecture

## 1. Overview
Eye Timer is a single-file Flask application that serves a self-contained front‑end implementing the 20‑20‑20 rule: every configurable X minutes of focus, look 20 feet away for Y seconds. All UI, logic, styles, and scripts are embedded in `eye-timer.py` and delivered via one HTML response. No build step or asset pipeline is required.

## 2. High-Level Components
| Layer | Responsibility |
|-------|----------------|
| Flask server | Serves root route and favicon; opens browser automatically. |
| HTML Template | Defines modal settings UI, timer display, controls, and progress indicators. |
| Tailwind CDN | Provides utility-first styling (loaded from CDN). |
| Font / Icons | Google Fonts + FontAwesome for typography and icons. |
| JavaScript App | Implements timer state, phase transitions, sound engine, settings persistence, and UI binding. |
| Web Audio API | Generates synthetic notification sounds; supports repeat count & delay. |
| Browser APIs | `Notification`, `localStorage`, `document.title` updates. |

## 3. Runtime Flow
1. Flask serves `/` returning embedded HTML/JS.
2. Page loads: `loadSettings()` pulls prior configuration from `localStorage`.
3. `resetTimer()` initializes focus phase and UI.
4. User starts timer: interval (`setInterval`) ticks once per second.
5. When `timeLeft` reaches 0, `switchPhase()` toggles between focus and break:
   - Updates durations & UI badges.
   - Plays sound via `audio.play(repeatCount, repeatDelay)`.
   - Sends desktop notification if enabled.
6. User interactions (skip, reset, save settings, toggles) mutate `appState` and re-render.

## 4. State Management
`appState` (in JS) holds:
- `isRunning`, `isFocus`, `timeLeft`, `totalTime`, `timerId`.
- `settings`: `focusTime`, `breakTime`, `soundType`, `volume`, `notificationsEnabled`, `repeatCount`, `repeatDelay`.

Persistence: `saveSettings()` writes a JSON blob to `localStorage` under `eyeTimerSettings`; `loadSettings()` reads and applies.

UI references are cached in `els` for efficient DOM access; no framework (React/Vue) is used.

## 5. Sound Engine
`SoundEngine` encapsulates Web Audio usage:
- Creates one `AudioContext`.
- `play(repeatCount, repeatDelay)` recursively schedules simple tones based on selected style (chime, digital, harp).
- Each play cycle instantiates oscillators with an envelope for quick attack and decay.

Extensibility: Additional sound profiles can be added by branching in the `play()` method or refactoring to a registry.

## 6. Notification Toggle Architecture
Independent from theme: UI knob and background classes manually controlled to reflect enabled/disabled without relying on Tailwind dark variant.

## 7. Settings Modal
Modal collects numeric inputs (focus minutes, break seconds, repeat count, repeat delay), sound selection, volume, theme toggle, notification toggle, plus a test sound button.
- `Save & Reset` applies new settings, persists them, and restarts timer.
- Test button previews current sound profile with current repeat settings.

## 8. Rendering & Feedback
- Timer updates once per second via `tick()`.
- Progress bar width derived from `timeLeft / totalTime`.
- Dynamic text rewrites: window title, header, bottom guidance line.
- Phase badges use distinct color sets for visual separation (brand vs emerald).

## 9. Error Handling & Resilience
Minimal explicit error handling; assumptions:
- Valid numeric input ranges (HTML `min`/`max` enforce bounds).
- Notification permission requested lazily on first start.
Potential enhancement: sanitize and clamp inputs in JS before applying.

## 10. Security Considerations
- No user-supplied HTML is rendered (XSS surface minimal).
- LocalStorage holds only simple numeric/string preferences (no secrets).
- Single-host localhost usage; no authentication needed.
- Flask debug disabled by default (`DEBUG = False`).

## 11. Performance Notes
- Lightweight—single HTML page and small JS object graph.
- Timer uses 1-second intervals (adequate granularity for purpose).
- Web Audio nodes are ephemeral; garbage collected after each phase trigger.

## 12. Extensibility Opportunities
| Area | Possible Improvement |
|------|----------------------|
| Sound | Add user-uploaded audio or buffer caching. |
| Scheduling | Allow custom cycles (e.g., Pomodoro variants). |
| Accessibility | Announce phase changes via ARIA live regions. |
| Persistence | Export/import settings profile. |
| UI | Add analytics (completed cycles counter). |
| Theming | Provide custom accent color picker. |

## 13. Potential Refactors
- Extract front-end into separate static files for easier maintenance.
- Introduce a tiny state machine to formalize phase transitions.
- Replace manual DOM updates with a reactive micro-library if complexity grows.
- Abstract notification + sound dispatch into unified "EventDispatcher" service.

## 14. Known Limitations
- Browser notifications may be blocked until user grants permission.
- Timer accuracy subject to tab throttling in background (Chrome may degrade intervals). Consider using `performance.now()` drift compensation if precision becomes critical.
- Sound repetition uses `setTimeout`; long delays could accumulate slight drift.

## 15. Quick Data Flow Summary
```
User Action --> DOM Event Listener --> Mutate appState.settings/state --> saveSettings()/resetTimer()/switchPhase
                                     |                                      |
                                     v                                      v
                              updateUI() -----------------> DOM updates (title, text, progress)
                                           \-> audio.play(repeatCount, repeatDelay)
                                           \-> Notification (if enabled & break phase)
```

## 16. Deployment & Execution
Run locally (with uv launcher shebang):
```bash
./eye-timer.py
```
(Flask serves on `http://localhost:5000` and auto-opens a browser.)

## 17. Future Testing Strategy
- Unit test pure functions (e.g., `formatTime`).
- Smoke test: simulate `switchPhase()` after manipulating `appState.timeLeft`.
- Visual regression: snapshot DOM states across phases.

---
This document should help onboard contributors and guide future enhancements while keeping the single-file simplicity in mind.
