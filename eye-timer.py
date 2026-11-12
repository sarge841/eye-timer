#!/usr/bin/env -S uv run
import os
import sys
import threading
import webbrowser
from flask import Flask, render_template_string, send_from_directory

# Configuration
# Allow environment overrides so the app can run inside containers and CI
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', str(5000)))
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('1', 'true', 'yes')

app = Flask(__name__)

# The complete frontend (HTML/CSS/JS) embedded in the Python file
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>20-20-20 Eye Timer</title>
    <link rel="icon" href="/favicon.png" type="image/png">
    <!-- Tailwind CSS for styling -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- FontAwesome for Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
    
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                        mono: ['JetBrains Mono', 'monospace'],
                    },
                    colors: {
                        brand: {
                            500: '#3b82f6',
                            600: '#2563eb',
                        }
                    }
                }
            }
        }
    </script>
    <style>
        /* Custom transitions */
        .fade-enter-active, .fade-leave-active { transition: opacity 0.5s; }
        .fade-enter, .fade-leave-to { opacity: 0; }
        
        /* Range Slider Styling */
        input[type=range] {
            -webkit-appearance: none;
            background: transparent;
        }
        input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none;
            height: 16px;
            width: 16px;
            border-radius: 50%;
            background: #3b82f6;
            cursor: pointer;
            margin-top: -6px; 
        }
        input[type=range]::-webkit-slider-runnable-track {
            width: 100%;
            height: 4px;
            cursor: pointer;
            background: #4b5563;
            border-radius: 2px;
        }

        /* Dynamic Screen / Anti-Burn-In Styles */
        body.burn-in-active {
            overflow: hidden;
            user-select: none;
        }
        html.dark body.burn-in-active {
            background-color: #020617;
        }
        html:not(.dark) body.burn-in-active {
            background-color: #f1f5f9;
        }

        /* Awake state in Dynamic Screen: semi-transparent card, full menu visibility */
        html.dark body.burn-in-active #main-card {
            background-color: rgba(30, 41, 59, 0.82);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-color: rgba(148, 163, 184, 0.22);
        }
        html:not(.dark) body.burn-in-active #main-card {
            background-color: rgba(255, 255, 255, 0.82);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-color: rgba(148, 163, 184, 0.3);
        }

        /* Simpler dimmed state after 15s inactivity: ultra-translucent card, hidden menu chrome, softer timer numbers */
        html.dark body.burn-in-active.burn-in-idle #main-card {
            background-color: rgba(15, 23, 42, 0.24);
            backdrop-filter: blur(6px);
            -webkit-backdrop-filter: blur(6px);
            border-color: rgba(148, 163, 184, 0.08);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        html:not(.dark) body.burn-in-active.burn-in-idle #main-card {
            background-color: rgba(255, 255, 255, 0.30);
            backdrop-filter: blur(6px);
            -webkit-backdrop-filter: blur(6px);
            border-color: rgba(148, 163, 184, 0.16);
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
        }

        /* Softer, lower-contrast (yet easily readable) timer digits when dimmed */
        html.dark body.burn-in-active.burn-in-idle #timer-display {
            color: rgba(203, 213, 225, 0.72);
            text-shadow: 0 2px 12px rgba(2, 6, 23, 0.45);
        }
        html:not(.dark) body.burn-in-active.burn-in-idle #timer-display {
            color: rgba(51, 65, 85, 0.72);
            text-shadow: 0 2px 12px rgba(255, 255, 255, 0.55);
        }

        body.burn-in-active #status-badge,
        body.burn-in-active #next-phase-text,
        body.burn-in-active #progress-bar-container {
            transition: opacity 0.6s ease;
        }
        body.burn-in-active.burn-in-idle #status-badge,
        body.burn-in-active.burn-in-idle #next-phase-text {
            opacity: 0.55;
        }
        body.burn-in-active.burn-in-idle #progress-bar-container {
            opacity: 0.3;
        }

        .burn-in-dimmable {
            transition: opacity 0.6s ease;
        }
        body.burn-in-active.burn-in-idle .burn-in-dimmable {
            opacity: 0;
            pointer-events: none;
        }

        /* Aurora animated blobs */
        @keyframes auroraFloat1 {
            0%, 100% { transform: translate(-15%, -10%) scale(1) rotate(0deg); }
            33% { transform: translate(20%, 15%) scale(1.2) rotate(45deg); }
            66% { transform: translate(-10%, 25%) scale(0.9) rotate(-30deg); }
        }
        @keyframes auroraFloat2 {
            0%, 100% { transform: translate(15%, 10%) scale(1.1) rotate(0deg); }
            33% { transform: translate(-25%, -15%) scale(0.9) rotate(-40deg); }
            66% { transform: translate(15%, -20%) scale(1.25) rotate(35deg); }
        }
        @keyframes auroraFloat3 {
            0%, 100% { transform: translate(0%, 20%) scale(0.95) rotate(0deg); }
            50% { transform: translate(20%, -20%) scale(1.15) rotate(60deg); }
        }
        .aurora-blob-1 { animation: auroraFloat1 18s ease-in-out infinite; }
        .aurora-blob-2 { animation: auroraFloat2 22s ease-in-out infinite; }
        .aurora-blob-3 { animation: auroraFloat3 26s ease-in-out infinite; }
    </style>
</head>
<body class="bg-gray-50 dark:bg-slate-900 text-slate-800 dark:text-slate-100 min-h-screen flex items-center justify-center transition-colors duration-300 relative">

    <!-- Dynamic Screen (Anti-Burn-In) Fullscreen Backdrop & Canvas -->
    <div id="burn-in-backdrop" class="fixed inset-0 pointer-events-none overflow-hidden z-0 hidden">
        <!-- Ambient drifting orbs for Drift mode -->
        <div id="burn-in-drift-glow" class="absolute inset-0 opacity-0 transition-opacity duration-700 flex items-center justify-center">
            <div id="burn-in-drift-orb" class="w-[28rem] h-[28rem] rounded-full blur-3xl transition-colors duration-1000 bg-blue-400/30 dark:bg-blue-500/20"></div>
            <div id="burn-in-drift-orb-secondary" class="w-[24rem] h-[24rem] rounded-full blur-3xl transition-colors duration-1000 bg-teal-300/25 dark:bg-indigo-500/15 absolute"></div>
        </div>
        <!-- Bouncing spotlight orb for Bounce mode -->
        <div id="burn-in-bounce-layer" class="absolute inset-0 opacity-0 transition-opacity duration-700 flex items-center justify-center">
            <div id="burn-in-bounce-orb" class="w-[26rem] h-[26rem] rounded-full blur-3xl transition-colors duration-700"></div>
        </div>
        <!-- Aurora layers for Aurora mode -->
        <div id="burn-in-aurora-layer" class="absolute inset-0 opacity-0 transition-opacity duration-700">
            <div class="aurora-blob-1 absolute top-1/4 left-1/4 w-[28rem] h-[28rem] rounded-full blur-3xl bg-sky-300/45 dark:bg-emerald-500/20"></div>
            <div class="aurora-blob-2 absolute bottom-1/4 right-1/4 w-[30rem] h-[30rem] rounded-full blur-3xl bg-purple-300/45 dark:bg-indigo-500/20"></div>
            <div class="aurora-blob-3 absolute top-1/3 right-1/3 w-[26rem] h-[26rem] rounded-full blur-3xl bg-teal-200/45 dark:bg-cyan-500/15"></div>
        </div>
        <!-- Particle Canvas for Starfield / Cosmic Drift mode -->
        <canvas id="burn-in-canvas" class="absolute inset-0 w-full h-full opacity-0 transition-opacity duration-700"></canvas>
    </div>

    <!-- Settings Modal (Placed outside #app so transform on #app does not affect fixed positioning) -->
    <div id="settings-modal" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 hidden flex items-center justify-center p-4">
        <div class="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-2xl w-full max-w-sm max-h-[90vh] overflow-y-auto border border-gray-200 dark:border-slate-700 transform transition-all scale-100">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-xl font-bold">Settings</h2>
                <button id="close-settings" class="text-gray-500 hover:text-brand-500 transition"><i class="fa-solid fa-xmark text-xl"></i></button>
            </div>

            <div class="space-y-5">
                <!-- Focus Duration -->
                <div>
                    <label class="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Focus Duration (minutes)</label>
                    <input type="number" id="focus-input" value="20" min="1" max="120" class="w-full bg-gray-100 dark:bg-slate-700 border-none rounded-lg px-4 py-2 focus:ring-2 focus:ring-brand-500 outline-none transition">
                </div>

                <!-- Break Duration -->
                <div>
                    <label class="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Break Duration (seconds)</label>
                    <input type="number" id="break-input" value="20" min="5" max="300" class="w-full bg-gray-100 dark:bg-slate-700 border-none rounded-lg px-4 py-2 focus:ring-2 focus:ring-brand-500 outline-none transition">
                </div>

                <!-- Sound Type -->
                <div>
                    <label class="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Notification Sound</label>
                    <div class="flex gap-3">
                        <select id="sound-type" class="flex-1 bg-gray-100 dark:bg-slate-700 border-none rounded-lg px-4 py-2 focus:ring-2 focus:ring-brand-500 outline-none transition">
                            <option value="chime">Gentle Chime</option>
                            <option value="digital">Digital Beep</option>
                            <option value="harp">Harp Flow</option>
                            <option value="hd2">Menacing (Kinda quiet)</option>
                        </select>
                        
                        <!-- TEST SOUND BUTTON -->
                        <button id="btn-test-sound" title="Test Sound" class="shrink-0 bg-gray-200 dark:bg-slate-600 text-gray-600 dark:text-gray-300 hover:text-brand-500 dark:hover:text-white hover:bg-brand-100 dark:hover:bg-brand-600 w-10 rounded-lg transition flex items-center justify-center border border-transparent hover:border-brand-500">
                            <i class="fa-solid fa-volume-high"></i>
                        </button>
                    </div>
                </div>

                <!-- Volume -->
                <div>
                    <div class="flex justify-between mb-1">
                        <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Volume</label>
                        <span id="volume-val" class="text-xs font-mono bg-slate-200 dark:bg-slate-600 px-2 rounded">50%</span>
                    </div>
                    <input type="range" id="volume-input" min="0" max="100" value="50" class="w-full">
                </div>

                <!-- Repeat Count -->
                <div>
                    <label class="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Repeat Count</label>
                    <input type="number" id="repeat-count" value="1" min="1" max="10" class="w-full bg-gray-100 dark:bg-slate-700 border-none rounded-lg px-4 py-2 focus:ring-2 focus:ring-brand-500 outline-none transition">
                </div>

                <!-- Repeat Delay -->
                <div>
                    <label class="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Repeat Delay (seconds)</label>
                    <input type="number" id="repeat-delay" value="1" min="1" max="10" class="w-full bg-gray-100 dark:bg-slate-700 border-none rounded-lg px-4 py-2 focus:ring-2 focus:ring-brand-500 outline-none transition">
                </div>

                <!-- Dark Mode Toggle -->
                <div class="flex items-center justify-between pt-2">
                    <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Dark Mode</label>
                    <button id="theme-toggle" class="w-12 h-6 bg-slate-300 dark:bg-brand-600 rounded-full relative transition-colors duration-300">
                        <div class="w-4 h-4 bg-white rounded-full absolute top-1 left-1 dark:left-7 transition-all duration-300 shadow-sm"></div>
                    </button>
                </div>

                <!-- Enable Notifications Toggle -->
                <div class="flex items-center justify-between pt-2">
                    <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Enable Desktop Notifications</label>
                    <!-- Independent toggle (not theme-dependent) -->
                    <button id="notification-toggle" class="w-12 h-6 rounded-full relative transition-colors duration-300 bg-brand-600">
                        <div class="w-4 h-4 bg-white rounded-full absolute top-1 left-7 transition-all duration-300 shadow-sm"></div>
                    </button>
                </div>

                <!-- Reverse Sound On Break End Toggle -->
                <div class="flex items-center justify-between pt-2">
                    <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Reverse Sound On Break End</label>
                    <button id="reverse-toggle" class="w-12 h-6 rounded-full relative transition-colors duration-300 bg-slate-300">
                        <div class="w-4 h-4 bg-white rounded-full absolute top-1 left-1 transition-all duration-300 shadow-sm"></div>
                    </button>
                </div>

                <!-- Screen Burn-In Protection Section -->
                <div class="pt-3 border-t border-gray-100 dark:border-slate-700/60 space-y-3">
                    <div class="flex items-center justify-between">
                        <div>
                            <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Dynamic Screen (Anti-Burn-In)</label>
                            <p class="text-xs text-gray-400 dark:text-gray-500">Simpler translucent timer with dynamic background</p>
                        </div>
                        <button id="burn-in-toggle" class="w-12 h-6 rounded-full relative transition-colors duration-300 bg-slate-300 shrink-0">
                            <div class="w-4 h-4 bg-white rounded-full absolute top-1 left-1 transition-all duration-300 shadow-sm"></div>
                        </button>
                    </div>

                    <div id="burn-in-mode-wrapper">
                        <label class="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Dynamic Screen Style</label>
                        <select id="burn-in-mode" class="w-full bg-gray-100 dark:bg-slate-700 border-none rounded-lg px-4 py-2 focus:ring-2 focus:ring-brand-500 outline-none transition text-sm">
                            <option value="drift">Ambient Orbs (Gentle Color Drift)</option>
                            <option value="bounce">Color Bounce (Drifting Spotlight)</option>
                            <option value="aurora">Ambient Aurora (Flowing Waves)</option>
                            <option value="starfield">Cosmic Drift (Starfield &amp; Particles)</option>
                        </select>
                    </div>

                    <!-- Dynamic Screen Style Tuning Section -->
                    <div id="burn-in-style-settings" class="bg-gray-50 dark:bg-slate-700/40 p-3.5 rounded-xl space-y-3 border border-gray-200/70 dark:border-slate-600/50">
                        <div class="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-400">
                            Dynamic Style Tuning
                        </div>

                        <!-- Movement Speed -->
                        <div>
                            <div class="flex justify-between mb-1">
                                <label for="burn-in-speed" class="block text-xs font-medium text-gray-500 dark:text-gray-400">Movement Speed</label>
                                <span id="burn-in-speed-val" class="text-xs font-mono bg-slate-200 dark:bg-slate-600 px-2 rounded">100%</span>
                            </div>
                            <input type="range" id="burn-in-speed" min="10" max="300" step="10" value="100" class="w-full">
                        </div>

                        <!-- Color Change Speed -->
                        <div>
                            <div class="flex justify-between mb-1">
                                <label for="burn-in-color-speed" class="block text-xs font-medium text-gray-500 dark:text-gray-400">Color Change Speed</label>
                                <span id="burn-in-color-speed-val" class="text-xs font-mono bg-slate-200 dark:bg-slate-600 px-2 rounded">100%</span>
                            </div>
                            <input type="range" id="burn-in-color-speed" min="10" max="300" step="10" value="100" class="w-full">
                        </div>

                        <!-- Particle Count -->
                        <div>
                            <div class="flex justify-between mb-1">
                                <label for="burn-in-particles" class="block text-xs font-medium text-gray-500 dark:text-gray-400">Particle Count</label>
                                <span id="burn-in-particles-val" class="text-xs font-mono bg-slate-200 dark:bg-slate-600 px-2 rounded">65</span>
                            </div>
                            <input type="range" id="burn-in-particles" min="10" max="250" step="5" value="65" class="w-full">
                        </div>
                    </div>
                </div>
            </div>

            <div class="mt-8">
                <button id="save-settings" class="w-full bg-brand-600 hover:bg-brand-500 text-white font-bold py-3 rounded-xl shadow-lg hover:shadow-brand-500/20 transition-all active:scale-95">
                    Save & Reset Timer
                </button>
            </div>
        </div>
    </div>

    <!-- Main App Container -->
    <div id="app" class="w-full max-w-md p-6 mx-4 relative z-10">

        <!-- Main Card -->
        <div id="main-card" class="bg-white dark:bg-slate-800 rounded-3xl shadow-2xl border border-gray-100 dark:border-slate-700 overflow-hidden transition-all duration-500">
            
            <!-- Header -->
            <div class="p-6 flex justify-between items-center border-b border-gray-100 dark:border-slate-700/50 burn-in-dimmable">
                <div class="flex items-center gap-3">
                    <div id="brand-icon-box" class="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center text-white transition-colors duration-500">
                        <i class="fa-solid fa-eye"></i>
                    </div>
                    <h1 class="font-bold text-lg tracking-tight">20-20-20</h1>
                </div>
                <div class="flex items-center gap-1">
                    <button id="toggle-fullscreen" title="Toggle Fullscreen" aria-label="Toggle Fullscreen" class="w-10 h-10 rounded-full hover:bg-gray-100 dark:hover:bg-slate-700 flex items-center justify-center transition text-gray-500 dark:text-gray-400">
                        <i id="fullscreen-icon" class="fa-solid fa-expand"></i>
                    </button>
                    <button id="open-settings" title="Settings" aria-label="Settings" class="w-10 h-10 rounded-full hover:bg-gray-100 dark:hover:bg-slate-700 flex items-center justify-center transition text-gray-500 dark:text-gray-400">
                        <i class="fa-solid fa-gear"></i>
                    </button>
                </div>
            </div>

            <!-- Timer Display -->
            <div class="p-10 flex flex-col items-center justify-center relative">
                
                <!-- Status Badge -->
                <div id="status-badge" class="mb-6 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-brand-100 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400 transition-colors">
                    Focus Time
                </div>

                <!-- Timer Text -->
                <div class="font-mono text-7xl font-bold tracking-tighter mb-2 tabular-nums transition-colors duration-500" id="timer-display">
                    20:00
                </div>
                
                <p class="text-gray-400 text-sm font-medium h-6" id="next-phase-text">Next: 20s Break</p>

                <!-- Circular Progress Background (Visual Flair) -->
                <div class="absolute inset-0 pointer-events-none opacity-5 burn-in-dimmable">
                    <svg class="w-full h-full" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="40" stroke="currentColor" stroke-width="1" fill="none" />
                    </svg>
                </div>
            </div>

            <!-- Progress Bar -->
            <div id="progress-bar-container" class="w-full h-2 bg-gray-100 dark:bg-slate-900/60">
                <div id="progress-bar" class="h-full bg-brand-500 transition-all duration-1000 ease-linear w-full"></div>
            </div>

            <!-- Controls -->
            <div id="controls-panel" class="p-6 grid grid-cols-3 gap-4 bg-gray-50 dark:bg-slate-800/50 burn-in-dimmable transition-colors duration-500">
                <button id="btn-reset" class="py-4 rounded-xl text-gray-500 hover:bg-gray-200 dark:hover:bg-slate-700 hover:text-gray-700 dark:hover:text-gray-200 transition flex flex-col items-center justify-center gap-1 group">
                    <i class="fa-solid fa-rotate-right text-xl group-hover:-rotate-180 transition-transform duration-500"></i>
                    <span class="text-xs font-bold">Reset</span>
                </button>

                <button id="btn-toggle" class="py-4 rounded-xl bg-brand-600 text-white shadow-lg shadow-brand-500/30 hover:bg-brand-500 hover:shadow-brand-500/50 transition transform hover:-translate-y-1 flex flex-col items-center justify-center gap-1">
                    <i id="play-icon" class="fa-solid fa-play text-xl pl-1"></i>
                    <span id="play-text" class="text-xs font-bold">Start</span>
                </button>

                <button id="btn-skip" class="py-4 rounded-xl text-gray-500 hover:bg-gray-200 dark:hover:bg-slate-700 hover:text-gray-700 dark:hover:text-gray-200 transition flex flex-col items-center justify-center gap-1">
                    <i class="fa-solid fa-forward-step text-xl"></i>
                    <span class="text-xs font-bold">Skip</span>
                </button>
            </div>
        </div>
        
        <div class="text-center mt-8 text-gray-400 text-xs burn-in-dimmable">
            <p id="footer-reminder-text">Look 20 feet away for 20 seconds every 20 minutes.</p>
        </div>
    </div>

    <!-- Audio Context Logic -->
    <script>
        // --- Audio Engine (Web Audio API) ---
        class SoundEngine {
            constructor() {
                this.ctx = new (window.AudioContext || window.webkitAudioContext)();
                this.volume = 0.5;
                this.type = 'chime';
            }

            setVolume(val) {
                this.volume = val / 100;
            }

            setType(type) {
                this.type = type;
            }

            resume() {
                if (this.ctx.state === 'suspended') {
                    this.ctx.resume();
                }
            }

            play(repeatCount = 1, repeatDelay = 1, reverse = false) {
                this.resume();
                const playSound = (count) => {
                    if (count <= 0) return;
                    const t = this.ctx.currentTime;
                    const gainNode = this.ctx.createGain();
                    gainNode.gain.value = this.volume;
                    gainNode.connect(this.ctx.destination);

                    if (!reverse) {
                        if (this.type === 'chime') {
                            this.playOscillator(660, 'sine', t, 0.1, gainNode);
                            this.playOscillator(880, 'sine', t + 0.15, 0.8, gainNode);
                        } else if (this.type === 'digital') {
                            this.playOscillator(800, 'square', t, 0.1, gainNode);
                            this.playOscillator(800, 'square', t + 0.15, 0.1, gainNode);
                        } else if (this.type === 'harp') {
                            [440, 554, 659, 880].forEach((freq, i) => {
                                this.playOscillator(freq, 'triangle', t + (i * 0.1), 1.5, gainNode);
                            });
                        } else if (this.type === 'hd2') {
                            // Start with low sound and build up
                            const delay = 1.25;
                            this.playOscillator(55, 'triangle', t, delay + 1, gainNode);
                            
                            const step1 = 5;
                            const step1duration = 0.75;
                            const step2duration = 0.75;
                            const shape = 'triangle';
                            [110, 117, 110, 131, 123, 117, 131, 123].forEach((freq, i) => {
                            // [220, 233, 220, 262, 247, 233, 262, 247].forEach((freq, i) => { // higher octave
                                if (i <= step1) {
                                    this.playOscillator(freq, shape, t + delay + (i * 0.20), step1duration, gainNode);
                                } else {
                                    this.playOscillator(freq, shape, t + delay + ((i - step1) * 0.10) + (step1 * 0.20), step2duration, gainNode);
                                }
                            });
                        }
                    } else {
                        // Reverse playback: invert the sequence/timing for a reverse effect
                        if (this.type === 'chime') {
                            // Play the higher tone first, then the lower with reversed timing
                            this.playOscillator(880, 'sine', t, 0.1, gainNode);
                            this.playOscillator(660, 'sine', t + 0.15, 0.8, gainNode);
                        } else if (this.type === 'digital') {
                            // Longer beep first then short beep
                            this.playOscillator(800, 'square', t, 0.1, gainNode);
                            this.playOscillator(800, 'square', t + 0.2, 0.15, gainNode);
                        } else if (this.type === 'harp') {
                            // Play the harp notes in reverse order
                            [880, 659, 554, 440].forEach((freq, i) => {
                                this.playOscillator(freq, 'triangle', t + (i * 0.1), 1.5, gainNode);
                            });
                        } else if (this.type === 'hd2') {
                            // Start with low sound and build up
                            const delay = 1.25;
                            this.playOscillator(55, 'triangle', t, delay + 1, gainNode);
                            
                            const step1 = 4;
                            const step1duration = 0.75;
                            const step2duration = 0.75;
                            const shape = 'triangle';
                            [110, 117, 110, 131, 123, 117, 110].forEach((freq, i) => {
                                if (i <= step1) {
                                    this.playOscillator(freq, shape, t + delay + (i * 0.20), step1duration, gainNode);
                                } else {
                                    this.playOscillator(freq, shape, t + delay + ((i - step1) * 0.10) + (step1 * 0.20), step2duration, gainNode);
                                }
                            });
                        }
                    }

                    setTimeout(() => playSound(count - 1), repeatDelay * 1000);
                };
                playSound(repeatCount);
            }

            playOscillator(freq, type, startTime, duration, outputNode) {
                const osc = this.ctx.createOscillator();
                osc.type = type;
                osc.frequency.value = freq;
                
                const envelope = this.ctx.createGain();
                envelope.gain.setValueAtTime(0, startTime);
                envelope.gain.linearRampToValueAtTime(1, startTime + 0.05);
                envelope.gain.exponentialRampToValueAtTime(0.01, startTime + duration);
                
                osc.connect(envelope);
                envelope.connect(outputNode);
                
                osc.start(startTime);
                osc.stop(startTime + duration);
            }
        }

        // --- App Logic ---
        
        // Default State
        const appState = {
            isRunning: false,
            isFocus: true, // true = 20 mins, false = 20 secs
            timeLeft: 20 * 60,
            totalTime: 20 * 60,
            timerId: null,
            // Timestamp-based timing to avoid background throttling issues
            startTimeMs: null,
            endTimeMs: null,
            remainingMs: 20 * 60 * 1000,
            finished: false,
            
            settings: {
                focusTime: 20 * 60,
                breakTime: 20,
                soundType: 'chime',
                volume: 50,
                notificationsEnabled: true,
                reverseOnBreakEnd: false,
                repeatCount: 1, // Default x
                repeatDelay: 1, // Default y
                burnInEnabled: false,
                burnInMode: 'drift', // 'drift' | 'bounce' | 'aurora' | 'starfield'
                burnInSpeed: 100, // 10 - 300 (%)
                burnInColorSpeed: 100, // 10 - 300 (%)
                burnInParticles: 65 // 10 - 250
            }
        };

        const VALID_BURN_IN_MODES = ['drift', 'bounce', 'aurora', 'starfield'];
        const audio = new SoundEngine();

        // DOM Elements
        const els = {
            appContainer: document.getElementById('app'),
            mainCard: document.getElementById('main-card'),
            controlsPanel: document.getElementById('controls-panel'),
            brandIconBox: document.getElementById('brand-icon-box'),
            display: document.getElementById('timer-display'),
            progressBar: document.getElementById('progress-bar'),
            statusBadge: document.getElementById('status-badge'),
            nextText: document.getElementById('next-phase-text'),
            btnToggle: document.getElementById('btn-toggle'),
            playIcon: document.getElementById('play-icon'),
            playText: document.getElementById('play-text'),
            btnReset: document.getElementById('btn-reset'),
            btnSkip: document.getElementById('btn-skip'),
            btnFullscreen: document.getElementById('toggle-fullscreen'),
            fullscreenIcon: document.getElementById('fullscreen-icon'),
            modal: document.getElementById('settings-modal'),
            burnInBackdrop: document.getElementById('burn-in-backdrop'),
            burnInDriftGlow: document.getElementById('burn-in-drift-glow'),
            burnInDriftOrb: document.getElementById('burn-in-drift-orb'),
            burnInDriftOrbSecondary: document.getElementById('burn-in-drift-orb-secondary'),
            burnInBounceLayer: document.getElementById('burn-in-bounce-layer'),
            burnInBounceOrb: document.getElementById('burn-in-bounce-orb'),
            burnInAuroraLayer: document.getElementById('burn-in-aurora-layer'),
            burnInCanvas: document.getElementById('burn-in-canvas'),
            inputs: {
                focus: document.getElementById('focus-input'),
                break: document.getElementById('break-input'),
                sound: document.getElementById('sound-type'),
                volume: document.getElementById('volume-input'),
                volDisplay: document.getElementById('volume-val'),
                theme: document.getElementById('theme-toggle'),
                reverse: document.getElementById('reverse-toggle'),
                testBtn: document.getElementById('btn-test-sound'),
                repeatCount: document.getElementById('repeat-count'),
                repeatDelay: document.getElementById('repeat-delay'),
                burnInToggle: document.getElementById('burn-in-toggle'),
                burnInMode: document.getElementById('burn-in-mode'),
                burnInSpeed: document.getElementById('burn-in-speed'),
                burnInSpeedVal: document.getElementById('burn-in-speed-val'),
                burnInColorSpeed: document.getElementById('burn-in-color-speed'),
                burnInColorSpeedVal: document.getElementById('burn-in-color-speed-val'),
                burnInParticles: document.getElementById('burn-in-particles'),
                burnInParticlesVal: document.getElementById('burn-in-particles-val')
            }
        };

        // --- Fullscreen Logic ---
        const isFullscreen = () => {
            return Boolean(document.fullscreenElement || document.webkitFullscreenElement);
        };

        const updateFullscreenUI = () => {
            if (!els.fullscreenIcon || !els.btnFullscreen) return;
            if (isFullscreen()) {
                els.fullscreenIcon.className = "fa-solid fa-compress";
                els.btnFullscreen.title = "Exit Fullscreen";
                els.btnFullscreen.setAttribute('aria-label', 'Exit Fullscreen');
            } else {
                els.fullscreenIcon.className = "fa-solid fa-expand";
                els.btnFullscreen.title = "Toggle Fullscreen";
                els.btnFullscreen.setAttribute('aria-label', 'Toggle Fullscreen');
            }
        };

        const toggleFullscreen = () => {
            try {
                if (!isFullscreen()) {
                    const docEl = document.documentElement;
                    if (docEl.requestFullscreen) {
                        docEl.requestFullscreen().catch(() => {});
                    } else if (docEl.webkitRequestFullscreen) {
                        docEl.webkitRequestFullscreen();
                    }
                } else {
                    if (document.exitFullscreen) {
                        document.exitFullscreen().catch(() => {});
                    } else if (document.webkitExitFullscreen) {
                        document.webkitExitFullscreen();
                    }
                }
            } catch (err) {
                // Ignore fullscreen errors in restricted environments
            }
        };

        // --- Dynamic Screen (Anti-Burn-In) Engine ---
        const BURN_IN_IDLE_TIMEOUT_MS = 15000; // Dim menu away after 15s of inactivity

        const BOUNCE_PALETTES = {
            dark: [
                { text: 'rgba(56, 189, 248, 0.92)', softText: 'rgba(125, 211, 252, 0.72)', orb: 'rgba(56, 189, 248, 0.22)', bar: '#0ea5e9' },
                { text: 'rgba(52, 211, 153, 0.92)', softText: 'rgba(110, 231, 183, 0.72)', orb: 'rgba(52, 211, 153, 0.22)', bar: '#10b981' },
                { text: 'rgba(167, 139, 250, 0.92)', softText: 'rgba(196, 181, 253, 0.72)', orb: 'rgba(167, 139, 250, 0.22)', bar: '#8b5cf6' },
                { text: 'rgba(251, 191, 36, 0.92)', softText: 'rgba(252, 211, 77, 0.72)', orb: 'rgba(251, 191, 36, 0.20)', bar: '#f59e0b' },
                { text: 'rgba(251, 113, 133, 0.92)', softText: 'rgba(253, 164, 175, 0.72)', orb: 'rgba(251, 113, 133, 0.22)', bar: '#f43f5e' },
                { text: 'rgba(45, 212, 191, 0.92)', softText: 'rgba(94, 234, 212, 0.72)', orb: 'rgba(45, 212, 191, 0.22)', bar: '#14b8a6' }
            ],
            light: [
                { text: 'rgba(37, 99, 235, 0.92)', softText: 'rgba(37, 99, 235, 0.70)', orb: 'rgba(59, 130, 246, 0.28)', bar: '#2563eb' },
                { text: 'rgba(5, 150, 105, 0.92)', softText: 'rgba(5, 150, 105, 0.70)', orb: 'rgba(16, 185, 129, 0.28)', bar: '#059669' },
                { text: 'rgba(124, 58, 237, 0.92)', softText: 'rgba(124, 58, 237, 0.70)', orb: 'rgba(139, 92, 246, 0.28)', bar: '#7c3aed' },
                { text: 'rgba(217, 119, 6, 0.92)', softText: 'rgba(180, 83, 9, 0.70)', orb: 'rgba(245, 158, 11, 0.28)', bar: '#d97706' },
                { text: 'rgba(225, 29, 72, 0.92)', softText: 'rgba(190, 18, 60, 0.70)', orb: 'rgba(244, 63, 94, 0.26)', bar: '#e11d48' },
                { text: 'rgba(13, 148, 136, 0.92)', softText: 'rgba(15, 118, 110, 0.70)', orb: 'rgba(20, 184, 166, 0.28)', bar: '#0d9488' }
            ]
        };

        const DRIFT_ORB_CLASSES = [
            'bg-blue-400/30 dark:bg-blue-500/20',
            'bg-emerald-400/30 dark:bg-emerald-500/20',
            'bg-purple-400/30 dark:bg-purple-500/20',
            'bg-teal-400/30 dark:bg-teal-500/20'
        ];

        const burnInState = {
            elapsed: 0,
            motionElapsed: 0,
            colorAngle: 0,
            lastFrameTime: null,
            orbX: 0,
            orbY: 0,
            vx: 85,
            vy: 65,
            bounceColorIdx: 0,
            lastBounceColorShift: 0,
            driftOrbIdx: 0,
            lastOrbShift: 0,
            idleTimer: null,
            particles: []
        };

        const isDarkMode = () => document.documentElement.classList.contains('dark');

        const createParticle = (w, h) => ({
            x: Math.random() * w,
            y: Math.random() * h,
            r: 1.2 + Math.random() * 2.4,
            vx: (Math.random() - 0.5) * 22,
            vy: -8 - Math.random() * 18,
            phase: Math.random() * Math.PI * 2,
            colorTimer: Math.random() * 4,
            colorSlot: Math.floor(Math.random() * 3)
        });

        const initParticles = () => {
            const w = window.innerWidth || 1024;
            const h = window.innerHeight || 768;
            if (els.burnInCanvas) {
                els.burnInCanvas.width = w;
                els.burnInCanvas.height = h;
            }
            const count = Math.max(10, Math.min(250, parseInt(appState.settings.burnInParticles) || 65));
            burnInState.particles = Array.from({ length: count }, () => createParticle(w, h));
        };

        const syncParticleCount = () => {
            const w = window.innerWidth || 1024;
            const h = window.innerHeight || 768;
            const target = Math.max(10, Math.min(250, parseInt(appState.settings.burnInParticles) || 65));
            while (burnInState.particles.length < target) {
                burnInState.particles.push(createParticle(w, h));
            }
            if (burnInState.particles.length > target) {
                burnInState.particles.length = target;
            }
        };

        const applyAuroraSpeed = () => {
            if (!els.burnInAuroraLayer) return;
            const speedMult = Math.max(0.1, (parseInt(appState.settings.burnInSpeed) || 100) / 100);
            const b1 = els.burnInAuroraLayer.querySelector('.aurora-blob-1');
            const b2 = els.burnInAuroraLayer.querySelector('.aurora-blob-2');
            const b3 = els.burnInAuroraLayer.querySelector('.aurora-blob-3');
            if (b1) b1.style.animationDuration = `${(18 / speedMult).toFixed(2)}s`;
            if (b2) b2.style.animationDuration = `${(22 / speedMult).toFixed(2)}s`;
            if (b3) b3.style.animationDuration = `${(26 / speedMult).toFixed(2)}s`;
        };

        const applyBounceAccent = () => {
            if (!appState.settings.burnInEnabled || appState.settings.burnInMode !== 'bounce') {
                els.display.style.color = '';
                els.progressBar.style.backgroundColor = '';
                els.brandIconBox.style.backgroundColor = '';
                if (els.burnInBounceOrb) els.burnInBounceOrb.style.backgroundColor = '';
                return;
            }
            const palette = isDarkMode() ? BOUNCE_PALETTES.dark : BOUNCE_PALETTES.light;
            const swatch = palette[burnInState.bounceColorIdx % palette.length];
            const isIdle = document.body.classList.contains('burn-in-idle');
            els.display.style.color = isIdle ? swatch.softText : swatch.text;
            els.progressBar.style.backgroundColor = swatch.bar;
            els.brandIconBox.style.backgroundColor = swatch.bar;
            if (els.burnInBounceOrb) {
                els.burnInBounceOrb.style.backgroundColor = swatch.orb;
            }
        };

        const scheduleIdleDim = () => {
            if (burnInState.idleTimer) clearTimeout(burnInState.idleTimer);
            if (!appState.settings.burnInEnabled) return;
            burnInState.idleTimer = setTimeout(() => {
                const modalOpen = !els.modal.classList.contains('hidden');
                if (appState.settings.burnInEnabled && !modalOpen) {
                    document.body.classList.add('burn-in-idle');
                    applyBounceAccent();
                }
            }, BURN_IN_IDLE_TIMEOUT_MS);
        };

        const wakeBurnInMenu = () => {
            if (!appState.settings.burnInEnabled) return;
            document.body.classList.remove('burn-in-idle');
            applyBounceAccent();
            scheduleIdleDim();
        };

        const updateToggleKnobUI = (btnEl, enabled) => {
            if (!btnEl) return;
            const knob = btnEl.querySelector('div');
            if (enabled) {
                btnEl.classList.add('bg-brand-600');
                btnEl.classList.remove('bg-slate-300');
                knob.classList.remove('left-1');
                knob.classList.add('left-7');
            } else {
                btnEl.classList.add('bg-slate-300');
                btnEl.classList.remove('bg-brand-600');
                knob.classList.remove('left-7');
                knob.classList.add('left-1');
            }
        };

        const applyBurnInState = (startDimmed = true) => {
            const enabled = Boolean(appState.settings.burnInEnabled);
            const mode = VALID_BURN_IN_MODES.includes(appState.settings.burnInMode)
                ? appState.settings.burnInMode
                : 'drift';
            appState.settings.burnInMode = mode;

            updateToggleKnobUI(els.inputs.burnInToggle, enabled);
            if (els.inputs.burnInMode) {
                els.inputs.burnInMode.value = mode;
            }
            if (els.inputs.burnInSpeed) {
                els.inputs.burnInSpeed.value = appState.settings.burnInSpeed;
                els.inputs.burnInSpeedVal.textContent = `${appState.settings.burnInSpeed}%`;
            }
            if (els.inputs.burnInColorSpeed) {
                els.inputs.burnInColorSpeed.value = appState.settings.burnInColorSpeed;
                els.inputs.burnInColorSpeedVal.textContent = `${appState.settings.burnInColorSpeed}%`;
            }
            if (els.inputs.burnInParticles) {
                els.inputs.burnInParticles.value = appState.settings.burnInParticles;
                els.inputs.burnInParticlesVal.textContent = `${appState.settings.burnInParticles}`;
            }

            syncParticleCount();
            applyAuroraSpeed();

            if (!enabled) {
                if (burnInState.idleTimer) clearTimeout(burnInState.idleTimer);
                document.body.classList.remove('burn-in-active', 'burn-in-idle');
                els.burnInBackdrop.classList.add('hidden');
                els.burnInDriftGlow.classList.replace('opacity-100', 'opacity-0');
                els.burnInBounceLayer.classList.replace('opacity-100', 'opacity-0');
                els.burnInAuroraLayer.classList.replace('opacity-100', 'opacity-0');
                els.burnInCanvas.classList.replace('opacity-100', 'opacity-0');
                els.burnInDriftOrb.style.transform = '';
                els.burnInDriftGlow.style.filter = '';
                els.burnInAuroraLayer.style.filter = '';
                if (els.burnInDriftOrbSecondary) els.burnInDriftOrbSecondary.style.transform = '';
                if (els.burnInBounceOrb) els.burnInBounceOrb.style.transform = '';
                burnInState.orbX = 0;
                burnInState.orbY = 0;
                burnInState.lastFrameTime = null;
                applyBounceAccent();
                return;
            }

            document.body.classList.add('burn-in-active');
            els.burnInBackdrop.classList.remove('hidden');

            // Toggle mode-specific backdrop layers
            const setLayerOpacity = (el, visible) => {
                if (!el) return;
                el.classList.toggle('opacity-100', visible);
                el.classList.toggle('opacity-0', !visible);
            };
            setLayerOpacity(els.burnInDriftGlow, mode === 'drift');
            setLayerOpacity(els.burnInBounceLayer, mode === 'bounce');
            setLayerOpacity(els.burnInAuroraLayer, mode === 'aurora');
            setLayerOpacity(els.burnInCanvas, mode === 'starfield');

            if (mode === 'starfield' && burnInState.particles.length === 0) {
                initParticles();
            }

            if (startDimmed) {
                document.body.classList.add('burn-in-idle');
                if (burnInState.idleTimer) clearTimeout(burnInState.idleTimer);
            } else {
                scheduleIdleDim();
            }
            applyBounceAccent();
        };

        const renderStarfield = (dt, speedMult, colorSpeedMult) => {
            if (!els.burnInCanvas) return;
            const ctx = els.burnInCanvas.getContext('2d');
            if (!ctx) return;
            const w = els.burnInCanvas.width;
            const h = els.burnInCanvas.height;
            ctx.clearRect(0, 0, w, h);

            const dark = isDarkMode();
            const darkColors = ['186, 230, 253', '199, 210, 254', '167, 243, 208', '245, 208, 254'];
            const lightColors = ['59, 130, 246', '99, 102, 241', '14, 165, 233', '16, 185, 129'];
            const palette = dark ? darkColors : lightColors;
            const shiftInterval = Math.max(0.4, 3.5 / colorSpeedMult);

            for (const p of burnInState.particles) {
                p.x += p.vx * dt * speedMult;
                p.y += p.vy * dt * speedMult;
                p.phase += dt * 1.8 * colorSpeedMult;
                p.colorTimer = (p.colorTimer || 0) + dt;
                if (p.colorTimer >= shiftInterval) {
                    p.colorTimer = 0;
                    p.colorSlot = (p.colorSlot + 1) % palette.length;
                }

                if (p.x < -10) p.x = w + 10;
                if (p.x > w + 10) p.x = -10;
                if (p.y < -10) p.y = h + 10;
                if (p.y > h + 10) p.y = -10;

                const alphaBase = dark ? 0.45 : 0.32;
                const alpha = alphaBase + Math.sin(p.phase) * 0.22;
                const rgb = palette[p.colorSlot % palette.length];

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(${rgb}, ${Math.max(0.08, alpha)})`;
                ctx.fill();
            }
        };

        const stepBurnInAnimation = (timestamp) => {
            if (!appState.settings.burnInEnabled || document.hidden) {
                burnInState.lastFrameTime = null;
                return;
            }

            if (burnInState.lastFrameTime === null) {
                burnInState.lastFrameTime = timestamp;
            }
            const dt = Math.min(0.05, (timestamp - burnInState.lastFrameTime) / 1000);
            burnInState.lastFrameTime = timestamp;

            const speedMult = Math.max(0.1, (parseInt(appState.settings.burnInSpeed) || 100) / 100);
            const colorSpeedMult = Math.max(0.1, (parseInt(appState.settings.burnInColorSpeed) || 100) / 100);

            const mode = appState.settings.burnInMode;
            if (mode === 'starfield') {
                renderStarfield(dt, speedMult, colorSpeedMult);
            }

            burnInState.elapsed += dt;
            burnInState.motionElapsed += dt * speedMult;
            burnInState.colorAngle = (burnInState.colorAngle + dt * 22 * colorSpeedMult) % 360;

            const t = burnInState.elapsed;
            const mt = burnInState.motionElapsed;

            const maxX = Math.max(80, window.innerWidth * 0.28);
            const maxY = Math.max(60, window.innerHeight * 0.24);

            if (mode === 'drift') {
                const x1 = Math.sin(mt * 0.35) * maxX;
                const y1 = Math.sin(mt * 0.23) * maxY;
                const x2 = Math.cos(mt * 0.27) * (maxX * 0.85);
                const y2 = Math.sin(mt * 0.41) * (maxY * 0.85);
                els.burnInDriftOrb.style.transform = `translate3d(${x1.toFixed(1)}px, ${y1.toFixed(1)}px, 0)`;
                if (els.burnInDriftOrbSecondary) {
                    els.burnInDriftOrbSecondary.style.transform = `translate3d(${x2.toFixed(1)}px, ${y2.toFixed(1)}px, 0)`;
                }
                els.burnInDriftGlow.style.filter = `hue-rotate(${burnInState.colorAngle.toFixed(1)}deg)`;

                const orbShiftInterval = Math.max(1.2, 8 / colorSpeedMult);
                if (t - burnInState.lastOrbShift > orbShiftInterval) {
                    burnInState.lastOrbShift = t;
                    burnInState.driftOrbIdx = (burnInState.driftOrbIdx + 1) % DRIFT_ORB_CLASSES.length;
                    els.burnInDriftOrb.className = `w-[28rem] h-[28rem] rounded-full blur-3xl transition-colors duration-1000 ${DRIFT_ORB_CLASSES[burnInState.driftOrbIdx]}`;
                }
            } else if (mode === 'bounce') {
                burnInState.orbX += burnInState.vx * dt * speedMult;
                burnInState.orbY += burnInState.vy * dt * speedMult;
                let bounced = false;

                if (burnInState.orbX >= maxX) {
                    burnInState.orbX = maxX;
                    burnInState.vx = -Math.abs(burnInState.vx);
                    bounced = true;
                } else if (burnInState.orbX <= -maxX) {
                    burnInState.orbX = -maxX;
                    burnInState.vx = Math.abs(burnInState.vx);
                    bounced = true;
                }

                if (burnInState.orbY >= maxY) {
                    burnInState.orbY = maxY;
                    burnInState.vy = -Math.abs(burnInState.vy);
                    bounced = true;
                } else if (burnInState.orbY <= -maxY) {
                    burnInState.orbY = -maxY;
                    burnInState.vy = Math.abs(burnInState.vy);
                    bounced = true;
                }

                if (els.burnInBounceOrb) {
                    els.burnInBounceOrb.style.transform = `translate3d(${burnInState.orbX.toFixed(1)}px, ${burnInState.orbY.toFixed(1)}px, 0)`;
                }

                const timedShiftInterval = Math.max(1.0, 6 / colorSpeedMult);
                if (bounced || (t - burnInState.lastBounceColorShift > timedShiftInterval)) {
                    burnInState.lastBounceColorShift = t;
                    burnInState.bounceColorIdx = (burnInState.bounceColorIdx + 1) % BOUNCE_PALETTES.dark.length;
                    applyBounceAccent();
                }
            } else if (mode === 'aurora') {
                els.burnInAuroraLayer.style.filter = `hue-rotate(${burnInState.colorAngle.toFixed(1)}deg)`;
            }
        };

        // --- Storage & Persistence ---
        const saveSettings = () => {
            const data = {
                focus: els.inputs.focus.value,
                break: els.inputs.break.value,
                sound: els.inputs.sound.value,
                volume: els.inputs.volume.value,
                reverse: appState.settings.reverseOnBreakEnd,
                repeatCount: els.inputs.repeatCount.value,
                repeatDelay: els.inputs.repeatDelay.value,
                theme: document.documentElement.classList.contains('dark') ? 'dark' : 'light',
                notificationsEnabled: appState.settings.notificationsEnabled,
                burnInEnabled: appState.settings.burnInEnabled,
                burnInMode: appState.settings.burnInMode,
                burnInSpeed: appState.settings.burnInSpeed,
                burnInColorSpeed: appState.settings.burnInColorSpeed,
                burnInParticles: appState.settings.burnInParticles
            };
            localStorage.setItem('eyeTimerSettings', JSON.stringify(data));
        };

        const loadSettings = () => {
            const saved = localStorage.getItem('eyeTimerSettings');
            if (saved) {
                const data = JSON.parse(saved);
                
                // Apply to inputs
                if(data.focus) els.inputs.focus.value = data.focus;
                if(data.break) els.inputs.break.value = data.break;
                if(data.sound) els.inputs.sound.value = data.sound;
                if(data.volume) {
                    els.inputs.volume.value = data.volume;
                    els.inputs.volDisplay.textContent = `${data.volume}%`;
                }
                if(data.repeatCount) els.inputs.repeatCount.value = data.repeatCount;
                if(data.repeatDelay) els.inputs.repeatDelay.value = data.repeatDelay;

                // Apply to App State
                if (data.focus) appState.settings.focusTime = parseInt(data.focus) * 60;
                if (data.break) appState.settings.breakTime = parseInt(data.break);
                if (data.sound) appState.settings.soundType = data.sound;
                if (data.volume) appState.settings.volume = parseInt(data.volume);
                appState.settings.notificationsEnabled = data.notificationsEnabled ?? true;
                if (data.repeatCount) appState.settings.repeatCount = parseInt(data.repeatCount);
                if (data.repeatDelay) appState.settings.repeatDelay = parseInt(data.repeatDelay);
                appState.settings.burnInEnabled = Boolean(data.burnInEnabled ?? false);
                if (data.burnInMode && VALID_BURN_IN_MODES.includes(data.burnInMode)) {
                    appState.settings.burnInMode = data.burnInMode;
                }
                if (data.burnInSpeed !== undefined) {
                    appState.settings.burnInSpeed = Math.max(10, Math.min(300, parseInt(data.burnInSpeed) || 100));
                }
                if (data.burnInColorSpeed !== undefined) {
                    appState.settings.burnInColorSpeed = Math.max(10, Math.min(300, parseInt(data.burnInColorSpeed) || 100));
                }
                if (data.burnInParticles !== undefined) {
                    appState.settings.burnInParticles = Math.max(10, Math.min(250, parseInt(data.burnInParticles) || 65));
                }

                // Apply to Audio
                audio.setVolume(appState.settings.volume);
                audio.setType(appState.settings.soundType);

                // Apply Theme
                if (data.theme === 'dark') {
                    document.documentElement.classList.add('dark');
                } else if (data.theme === 'light') {
                    document.documentElement.classList.remove('dark');
                }

                // Apply Notification Toggle (independent of theme)
                const notifBtn = document.getElementById('notification-toggle');
                updateToggleKnobUI(notifBtn, appState.settings.notificationsEnabled);

                // Apply Reverse Toggle
                const revBtn = document.getElementById('reverse-toggle');
                appState.settings.reverseOnBreakEnd = data.reverse ?? false;
                updateToggleKnobUI(revBtn, appState.settings.reverseOnBreakEnd);

                // Apply Dynamic Screen / Burn-In Protection
                applyBurnInState();
            } else {
                // If no save found, just ensure theme matches system or default
                if (localStorage.getItem('theme') === 'light') {
                    document.documentElement.classList.remove('dark');
                }
                applyBurnInState();
            }
        };

        // Helpers
        const formatTime = (s) => {
            const mins = Math.floor(s / 60);
            const secs = s % 60;
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        };

        const updateUI = () => {
            els.display.textContent = formatTime(appState.timeLeft);
            const pct = (appState.timeLeft / appState.totalTime) * 100;
            els.progressBar.style.width = `${pct}%`;

            // Update the title dynamically
            const focusMinutes = appState.settings.focusTime / 60;
            const breakSeconds = appState.settings.breakTime;
            document.title = `${focusMinutes}-${breakSeconds}-20 Eye Timer`;

            // Update the bottom text dynamically
            const bottomText = `Look 20 feet away for ${breakSeconds} seconds every ${focusMinutes} minutes.`;
            document.querySelector('.text-center p').textContent = bottomText;

            // Update the H1 dynamically
            const headerText = `${focusMinutes}-${breakSeconds}-20`;
            document.querySelector('h1.font-bold').textContent = headerText;
        };

        const switchPhase = () => {
                // Determine the upcoming phase (we haven't toggled yet)
                const nextIsFocus = !appState.isFocus;
                // If we're moving into focus (i.e., break ended) and reverse is enabled, play reversed sound
                const reverseFlag = nextIsFocus && appState.settings.reverseOnBreakEnd;
                audio.play(appState.settings.repeatCount, appState.settings.repeatDelay, reverseFlag);
                appState.isFocus = nextIsFocus;

                if (appState.isFocus) {
                    // Switching to Focus
                    appState.totalTime = appState.settings.focusTime;
                    els.statusBadge.textContent = "Focus Time";
                    els.statusBadge.className = "mb-6 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-brand-100 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400 transition-colors";
                    els.nextText.textContent = `Next: ${appState.settings.breakTime}s Break`;
                } else {
                    // Switching to Break
                    appState.totalTime = appState.settings.breakTime;
                    els.statusBadge.textContent = "Look Away (20ft)";
                    els.statusBadge.className = "mb-6 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400 transition-colors";
                    els.nextText.textContent = `Next: ${appState.settings.focusTime / 60}m Focus`;

                    // Update notification dynamically
                    if (appState.settings.notificationsEnabled) {
                        new Notification("Eye Break!", { body: `Look 20 feet away for ${appState.settings.breakTime} seconds.` });
                    }
                }

            // Initialize timestamps for the new phase
            appState.totalTime = appState.isFocus ? appState.settings.focusTime : appState.settings.breakTime;
            appState.remainingMs = appState.totalTime * 1000;
            appState.startTimeMs = Date.now();
            appState.endTimeMs = appState.startTimeMs + appState.remainingMs;
            appState.timeLeft = Math.ceil(appState.remainingMs / 1000);
            appState.finished = false;
            updateUI();
        };

        const tick = () => {
            // Only update while the timer is actively running
            if (!appState.isRunning) return;

            // If no endTime set, nothing to do
            if (!appState.endTimeMs) return;

            // Compute remaining ms from wall-clock time so background throttling doesn't break logic
            let remainingMs = appState.endTimeMs - Date.now();
            // If we've missed the deadline (user was away), advance phases until caught up
            while (remainingMs <= 0 && !appState.finished) {
                // Mark finished for this phase to avoid infinite loop if switchPhase doesn't advance time
                appState.finished = true;
                switchPhase();
                // After switching phase, recompute remainingMs for the new phase
                if (!appState.endTimeMs) return;
                remainingMs = appState.endTimeMs - Date.now();
            }

            appState.remainingMs = Math.max(0, remainingMs);
            appState.timeLeft = Math.max(0, Math.ceil(appState.remainingMs / 1000));
            updateUI();
        };

        const toggleTimer = () => {
            audio.resume(); // Ensure audio context is active on click

            if (appState.isRunning) {
                // Snapshot remaining time and clear the endTime to avoid stale timestamps
                if (appState.endTimeMs) {
                    appState.remainingMs = Math.max(0, appState.endTimeMs - Date.now());
                    appState.timeLeft = Math.max(0, Math.ceil(appState.remainingMs / 1000));
                    appState.endTimeMs = null;
                }

                clearInterval(appState.timerId);
                appState.isRunning = false;
                els.playIcon.className = "fa-solid fa-play text-xl pl-1";
                els.playText.textContent = "Resume";
                els.btnToggle.classList.remove('bg-amber-500', 'hover:bg-amber-600');
                els.btnToggle.classList.add('bg-brand-600', 'hover:bg-brand-500');
            } else {
                // Request notification permission on first start
                if (Notification.permission !== "granted") Notification.requestPermission();

                // Initialize timestamps based on remainingMs (preserve paused remaining time)
                appState.startTimeMs = Date.now();
                appState.endTimeMs = appState.startTimeMs + (appState.remainingMs || (appState.totalTime * 1000));

                // Mark running, update UI, and immediately reconcile time (handles any missed phases)
                appState.isRunning = true;
                els.playIcon.className = "fa-solid fa-pause text-xl";
                els.playText.textContent = "Pause";
                els.btnToggle.classList.remove('bg-brand-600', 'hover:bg-brand-500');
                els.btnToggle.classList.add('bg-amber-500', 'hover:bg-amber-600');

                // Run a tick immediately so we don't wait the first interval and to fast-forward if needed
                tick();

                // Start the main updater (timestamp-based). Frequency isn't critical because tick uses wall-clock.
                appState.timerId = setInterval(tick, 1000);
            }
        };

        const resetTimer = () => {
            clearInterval(appState.timerId);
            appState.isRunning = false;
            appState.isFocus = true; // Always reset to focus
            appState.totalTime = appState.settings.focusTime;
            appState.timeLeft = appState.totalTime;
            appState.remainingMs = appState.totalTime * 1000;
            appState.startTimeMs = Date.now();
            appState.endTimeMs = appState.startTimeMs + appState.remainingMs;
            appState.finished = false;
            
            els.playIcon.className = "fa-solid fa-play text-xl pl-1";
            els.playText.textContent = "Start";
            els.btnToggle.classList.remove('bg-amber-500', 'hover:bg-amber-600');
            els.btnToggle.classList.add('bg-brand-600', 'hover:bg-brand-500');
            
            els.statusBadge.textContent = "Focus Time";
            els.statusBadge.className = "mb-6 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-brand-100 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400 transition-colors";
            
            els.nextText.textContent = `Next: ${appState.settings.breakTime}s Break`;
            
            updateUI();
        };

        // --- Event Listeners ---

        els.btnToggle.addEventListener('click', toggleTimer);
        els.btnReset.addEventListener('click', resetTimer);
        els.btnSkip.addEventListener('click', () => {
            audio.resume();
            switchPhase();
        });

        // Fullscreen Button & Events
        els.btnFullscreen.addEventListener('click', toggleFullscreen);
        document.addEventListener('fullscreenchange', updateFullscreenUI);
        document.addEventListener('webkitfullscreenchange', updateFullscreenUI);

        // Test Sound Button
        els.inputs.testBtn.addEventListener('click', () => {
            audio.resume();
            audio.setType(els.inputs.sound.value);
            audio.play(parseInt(els.inputs.repeatCount.value) || 1, parseInt(els.inputs.repeatDelay.value) || 1);
        });

        // Settings Modal
        document.getElementById('open-settings').addEventListener('click', () => {
            if (burnInState.idleTimer) clearTimeout(burnInState.idleTimer);
            els.modal.classList.remove('hidden');
        });

        document.getElementById('close-settings').addEventListener('click', () => {
            els.modal.classList.add('hidden');
            if (appState.settings.burnInEnabled && !document.body.classList.contains('burn-in-idle')) {
                scheduleIdleDim();
            }
        });

        // Volume Slider
        els.inputs.volume.addEventListener('input', (e) => {
            const val = e.target.value;
            els.inputs.volDisplay.textContent = `${val}%`;
            audio.setVolume(val);
            // We don't save immediately on slide to avoid spamming storage, 
            // but we could. It's saved on "Save & Reset" anyway.
        });

        // Save Settings
        document.getElementById('save-settings').addEventListener('click', () => {
            const newFocus = parseInt(els.inputs.focus.value) * 60;
            const newBreak = parseInt(els.inputs.break.value);
            
            appState.settings.focusTime = newFocus;
            appState.settings.breakTime = newBreak;
            appState.settings.soundType = els.inputs.sound.value;
            appState.settings.volume = parseInt(els.inputs.volume.value);
            appState.settings.repeatCount = parseInt(els.inputs.repeatCount.value);
            appState.settings.repeatDelay = parseInt(els.inputs.repeatDelay.value);
            appState.settings.burnInMode = els.inputs.burnInMode.value;
            appState.settings.burnInSpeed = parseInt(els.inputs.burnInSpeed.value) || 100;
            appState.settings.burnInColorSpeed = parseInt(els.inputs.burnInColorSpeed.value) || 100;
            appState.settings.burnInParticles = parseInt(els.inputs.burnInParticles.value) || 65;
            
            audio.setType(appState.settings.soundType);
            applyBurnInState(true);
            
            saveSettings(); // Save to LocalStorage
            resetTimer();
            els.modal.classList.add('hidden');
        });

        // Theme Toggle
        els.inputs.theme.addEventListener('click', () => {
            document.documentElement.classList.toggle('dark');
            applyBounceAccent(); // Ensure dynamic bounce palette adapts to theme
            saveSettings(); // Save immediately on theme toggle
        });

        // Notification Toggle (independent of theme)
        const notificationToggle = document.getElementById('notification-toggle');
        notificationToggle.addEventListener('click', () => {
            const enabled = !appState.settings.notificationsEnabled;
            appState.settings.notificationsEnabled = enabled;
            updateToggleKnobUI(notificationToggle, enabled);
            saveSettings();
        });

        // Reverse Toggle (play reverse sound when break ends)
        const reverseToggleBtn = document.getElementById('reverse-toggle');
        reverseToggleBtn.addEventListener('click', () => {
            const enabled = !appState.settings.reverseOnBreakEnd;
            appState.settings.reverseOnBreakEnd = enabled;
            updateToggleKnobUI(reverseToggleBtn, enabled);
            saveSettings();
        });

        // Dynamic Screen (Anti-Burn-In) Toggle, Mode Selector & Tuning Sliders
        els.inputs.burnInToggle.addEventListener('click', () => {
            appState.settings.burnInEnabled = !appState.settings.burnInEnabled;
            applyBurnInState(true);
            saveSettings();
        });

        els.inputs.burnInMode.addEventListener('change', (e) => {
            const selectedMode = e.target.value;
            if (VALID_BURN_IN_MODES.includes(selectedMode)) {
                appState.settings.burnInMode = selectedMode;
                applyBurnInState(true);
                saveSettings();
            }
        });

        els.inputs.burnInSpeed.addEventListener('input', (e) => {
            const val = Math.max(10, Math.min(300, parseInt(e.target.value) || 100));
            appState.settings.burnInSpeed = val;
            els.inputs.burnInSpeedVal.textContent = `${val}%`;
            applyAuroraSpeed();
            saveSettings();
        });

        els.inputs.burnInColorSpeed.addEventListener('input', (e) => {
            const val = Math.max(10, Math.min(300, parseInt(e.target.value) || 100));
            appState.settings.burnInColorSpeed = val;
            els.inputs.burnInColorSpeedVal.textContent = `${val}%`;
            saveSettings();
        });

        els.inputs.burnInParticles.addEventListener('input', (e) => {
            const val = Math.max(10, Math.min(250, parseInt(e.target.value) || 65));
            appState.settings.burnInParticles = val;
            els.inputs.burnInParticlesVal.textContent = `${val}`;
            syncParticleCount();
            saveSettings();
        });

        // Click anywhere on the screen (outside Settings modal) to show the full timer menu for 15s
        document.addEventListener('click', (e) => {
            if (!appState.settings.burnInEnabled) return;
            if (!els.modal.classList.contains('hidden') || els.modal.contains(e.target)) return;
            wakeBurnInMenu();
        });

        window.addEventListener('resize', () => {
            if (appState.settings.burnInEnabled && appState.settings.burnInMode === 'starfield') {
                initParticles();
            }
        });

        // Init
        initParticles();
        loadSettings(); // Load from storage
        resetTimer();   // Initialize with loaded settings
        updateFullscreenUI();

        // If page visibility changes (user returns), recompute immediately
        document.addEventListener('visibilitychange', () => {
            // Only run tick when the timer is actively running
            if (!document.hidden && appState.isRunning) tick();
        });

        // rAF loop for smooth progress and anti-burn-in animations when visible; setInterval fallback handles backgrounded checks
        const rAFLoop = (timestamp) => {
            if (appState.isRunning && !document.hidden && appState.endTimeMs) {
                // Light-weight update for progress bar and small visual smoothness
                const remainingMs = Math.max(0, appState.endTimeMs - Date.now());
                const remainingSec = Math.ceil(remainingMs / 1000);
                const pct = (remainingSec / appState.totalTime) * 100;
                els.progressBar.style.width = `${pct}%`;
            }
            if (appState.settings.burnInEnabled && !document.hidden) {
                stepBurnInAnimation(timestamp);
            }
            requestAnimationFrame(rAFLoop);
        };
        requestAnimationFrame(rAFLoop);

    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# Serve the favicon
@app.route('/favicon.png')
def favicon():
    return send_from_directory(os.path.dirname(__file__), 'favicon.png')

def open_browser():
    """Opens the browser automatically after a short delay."""
    webbrowser.open(f'http://{HOST}:{PORT}')

if __name__ == '__main__':
    # # Start the browser in a separate thread to avoid blocking the server start
    # if not os.environ.get("WERKZEUG_RUN_MAIN"): # Prevent opening twice on reloads
    #     threading.Timer(1.0, open_browser).start()
    
    print(f"Starting Eye Timer on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)