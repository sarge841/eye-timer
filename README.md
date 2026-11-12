# Eye Timer

Eye Timer is a lightweight productivity and eye-care web application implementing the **20-20-20 rule** (every 20 minutes of focus, look 20 feet away for 20 seconds). It features customizable durations, synthesized Web Audio notifications, fullscreen support, and a dynamic anti-burn-in screen mode.

## Disclaimer
This application was built entirely using AI tools and assistance. While every effort has been made to ensure its functionality and reliability, users are encouraged to review the code and adapt it to their specific needs.

## Features
- **Customizable 20-20-20 Durations**: Configure focus duration (minutes) and break duration (seconds).
- **Fullscreen Mode**: Toggle fullscreen directly from the expand/compress icon right next to the settings gear in the header.
- **Dynamic Screen (Anti-Burn-In / Screensaver)**: Prevent OLED burn-in and monitor image retention while keeping the countdown timer, phase status, and progress visible. Includes 4 theme-aware styles that respect both Dark Mode and Light Mode:
  - **Gentle Orbit (Pixel Drift)**: Smoothly orbits the timer across the screen with an ambient color-shifting glow.
  - **DVD Bounce (Color Shift)**: Bounces the timer off the screen edges, cycling accent colors on every bounce.
  - **Ambient Aurora (Waves & Wander)**: Flowing aurora borealis waves behind a translucent wandering glass HUD.
  - **Cosmic Drift (Particles & Wander)**: Animated drifting particle starfield with a wandering translucent timer HUD.
  - Automatically dims static chrome when idle and pauses movement on hover so buttons are always easy to click.
- **Synthesized Audio Notifications**: Built-in Web Audio API synthesizer (`Gentle Chime`, `Digital Beep`, `Harp Flow`, `Menacing`) with adjustable volume, repeat count, repeat delay, and optional reverse sound playback when a break ends.
- **Dark Mode & Desktop Notifications**: One-click toggles persisted in `localStorage`.
- **Accurate Wall-Clock Timing**: Uses timestamp deltas so browser background tab throttling never causes timer drift.

## Prerequisites
- Python 3.11+ (or 3.14+ via `uv`)
- [`uv`](https://docs.astral.sh/uv/) installed for running the app and tests

## Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd eye-timer
   ```
2. Sync dependencies with `uv`:
   ```bash
   uv sync
   ```

## Running the Application
To start the application, use `uv`:
```bash
uv run eye-timer.py
```
The server starts on `http://0.0.0.0:5000` by default (configurable via `HOST`, `PORT`, and `DEBUG` environment variables).

## Running Tests
To run the unit and frontend integration test suite:
```bash
uv run tests/test_eye_timer.py
```
Or via standard `unittest` discovery (as used in CI):
```bash
uv run python -m unittest discover -v
```

## Documentation & AI Agent Orientation
- **[`AGENTS.md`](AGENTS.md)**: Fast-start orientation guide for AI coding agents (architecture overview, key commands, subsystem map, and layout/CSS gotchas).
- **[`docs/architecture.md`](docs/architecture.md)**: Detailed technical documentation of the single-file Flask + vanilla JS architecture.

## Contributing
1. Fork the repository.
2. Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes and push to your fork:
   ```bash
   git commit -m "Description of changes"
   git push origin feature-name
   ```
4. Open a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
