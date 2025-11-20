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
    </style>
</head>
<body class="bg-gray-50 dark:bg-slate-900 text-slate-800 dark:text-slate-100 min-h-screen flex items-center justify-center transition-colors duration-300">

    <!-- Main App Container -->
    <div id="app" class="w-full max-w-md p-6 mx-4 relative">
        
        <!-- Settings Modal -->
        <div id="settings-modal" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 hidden flex items-center justify-center">
            <div class="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-2xl w-full max-w-sm border border-gray-200 dark:border-slate-700 transform transition-all scale-100">
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
                        <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Enable Notifications</label>
                        <!-- Independent toggle (not theme-dependent) -->
                        <button id="notification-toggle" class="w-12 h-6 rounded-full relative transition-colors duration-300 bg-brand-600">
                            <div class="w-4 h-4 bg-white rounded-full absolute top-1 left-7 transition-all duration-300 shadow-sm"></div>
                        </button>
                    </div>
                </div>

                <div class="mt-8">
                    <button id="save-settings" class="w-full bg-brand-600 hover:bg-brand-500 text-white font-bold py-3 rounded-xl shadow-lg hover:shadow-brand-500/20 transition-all active:scale-95">
                        Save & Reset Timer
                    </button>
                </div>
            </div>
        </div>

        <!-- Main Card -->
        <div class="bg-white dark:bg-slate-800 rounded-3xl shadow-2xl border border-gray-100 dark:border-slate-700 overflow-hidden">
            
            <!-- Header -->
            <div class="p-6 flex justify-between items-center border-b border-gray-100 dark:border-slate-700/50">
                <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center text-white">
                        <i class="fa-solid fa-eye"></i>
                    </div>
                    <h1 class="font-bold text-lg tracking-tight">20-20-20</h1>
                </div>
                <button id="open-settings" class="w-10 h-10 rounded-full hover:bg-gray-100 dark:hover:bg-slate-700 flex items-center justify-center transition text-gray-500 dark:text-gray-400">
                    <i class="fa-solid fa-gear"></i>
                </button>
            </div>

            <!-- Timer Display -->
            <div class="p-10 flex flex-col items-center justify-center relative">
                
                <!-- Status Badge -->
                <div id="status-badge" class="mb-6 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-brand-100 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400 transition-colors">
                    Focus Time
                </div>

                <!-- Timer Text -->
                <div class="font-mono text-7xl font-bold tracking-tighter mb-2 tabular-nums" id="timer-display">
                    20:00
                </div>
                
                <p class="text-gray-400 text-sm font-medium h-6" id="next-phase-text">Next: 20s Break</p>

                <!-- Circular Progress Background (Visual Flair) -->
                <div class="absolute inset-0 pointer-events-none opacity-5">
                    <svg class="w-full h-full" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="40" stroke="currentColor" stroke-width="1" fill="none" />
                    </svg>
                </div>
            </div>

            <!-- Progress Bar -->
            <div class="w-full h-2 bg-gray-100 dark:bg-slate-900">
                <div id="progress-bar" class="h-full bg-brand-500 transition-all duration-1000 ease-linear w-full"></div>
            </div>

            <!-- Controls -->
            <div class="p-6 grid grid-cols-3 gap-4 bg-gray-50 dark:bg-slate-800/50">
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
        
        <div class="text-center mt-8 text-gray-400 text-xs">
            <p>Look 20 feet away for 20 seconds every 20 minutes.</p>
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

            play(repeatCount = 1, repeatDelay = 1) {
                this.resume();
                const playSound = (count) => {
                    if (count <= 0) return;
                    const t = this.ctx.currentTime;
                    const gainNode = this.ctx.createGain();
                    gainNode.gain.value = this.volume;
                    gainNode.connect(this.ctx.destination);

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
                repeatCount: 1, // Default x
                repeatDelay: 1  // Default y
            }
        };

        const audio = new SoundEngine();

        // DOM Elements
        const els = {
            display: document.getElementById('timer-display'),
            progressBar: document.getElementById('progress-bar'),
            statusBadge: document.getElementById('status-badge'),
            nextText: document.getElementById('next-phase-text'),
            btnToggle: document.getElementById('btn-toggle'),
            playIcon: document.getElementById('play-icon'),
            playText: document.getElementById('play-text'),
            btnReset: document.getElementById('btn-reset'),
            btnSkip: document.getElementById('btn-skip'),
            modal: document.getElementById('settings-modal'),
            inputs: {
                focus: document.getElementById('focus-input'),
                break: document.getElementById('break-input'),
                sound: document.getElementById('sound-type'),
                volume: document.getElementById('volume-input'),
                volDisplay: document.getElementById('volume-val'),
                theme: document.getElementById('theme-toggle'),
                testBtn: document.getElementById('btn-test-sound'),
                repeatCount: document.getElementById('repeat-count'),
                repeatDelay: document.getElementById('repeat-delay')
            }
        };

        // --- Storage & Persistence ---
        const saveSettings = () => {
            const data = {
                focus: els.inputs.focus.value,
                break: els.inputs.break.value,
                sound: els.inputs.sound.value,
                volume: els.inputs.volume.value,
                repeatCount: els.inputs.repeatCount.value,
                repeatDelay: els.inputs.repeatDelay.value,
                theme: document.documentElement.classList.contains('dark') ? 'dark' : 'light',
                notificationsEnabled: appState.settings.notificationsEnabled
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
                appState.settings.focusTime = parseInt(data.focus) * 60;
                appState.settings.breakTime = parseInt(data.break);
                appState.settings.soundType = data.sound;
                appState.settings.volume = parseInt(data.volume);
                appState.settings.notificationsEnabled = data.notificationsEnabled ?? true;
                appState.settings.repeatCount = parseInt(data.repeatCount);
                appState.settings.repeatDelay = parseInt(data.repeatDelay);

                // Apply to Audio
                audio.setVolume(appState.settings.volume);
                audio.setType(appState.settings.soundType);

                // Apply Theme
                if (data.theme === 'dark') {
                    document.documentElement.classList.add('dark');
                } else {
                    document.documentElement.classList.remove('dark');
                }

                // Apply Notification Toggle (independent of theme)
                const notifBtn = document.getElementById('notification-toggle');
                const notifKnob = notifBtn.querySelector('div');
                if (appState.settings.notificationsEnabled) {
                    notifBtn.classList.add('bg-brand-600');
                    notifBtn.classList.remove('bg-slate-300');
                    notifKnob.classList.remove('left-1');
                    notifKnob.classList.add('left-7');
                } else {
                    notifBtn.classList.add('bg-slate-300');
                    notifBtn.classList.remove('bg-brand-600');
                    notifKnob.classList.remove('left-7');
                    notifKnob.classList.add('left-1');
                }
            } else {
                // If no save found, just ensure theme matches system or default
                if (localStorage.getItem('theme') === 'light') {
                    document.documentElement.classList.remove('dark');
                }
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
            // Play notification sound with repeats
            audio.play(appState.settings.repeatCount, appState.settings.repeatDelay);
            appState.isFocus = !appState.isFocus;

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
                // Start the main updater (timestamp-based). Frequency isn't critical because tick uses wall-clock.
                appState.timerId = setInterval(tick, 1000);
                appState.isRunning = true;
                els.playIcon.className = "fa-solid fa-pause text-xl";
                els.playText.textContent = "Pause";
                els.btnToggle.classList.remove('bg-brand-600', 'hover:bg-brand-500');
                els.btnToggle.classList.add('bg-amber-500', 'hover:bg-amber-600');
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

        // Test Sound Button
        els.inputs.testBtn.addEventListener('click', () => {
            audio.resume();
            audio.setType(els.inputs.sound.value);
            audio.play(parseInt(els.inputs.repeatCount.value) || 1, parseInt(els.inputs.repeatDelay.value) || 1);
        });

        // Settings Modal
        document.getElementById('open-settings').addEventListener('click', () => {
            els.modal.classList.remove('hidden');
        });

        document.getElementById('close-settings').addEventListener('click', () => {
            els.modal.classList.add('hidden');
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
            
            audio.setType(appState.settings.soundType);
            
            saveSettings(); // Save to LocalStorage
            resetTimer();
            els.modal.classList.add('hidden');
        });

        // Theme Toggle
        els.inputs.theme.addEventListener('click', () => {
            document.documentElement.classList.toggle('dark');
            saveSettings(); // Save immediately on theme toggle
        });

        // Notification Toggle (independent of theme)
        const notificationToggle = document.getElementById('notification-toggle');
        notificationToggle.addEventListener('click', () => {
            const enabled = !appState.settings.notificationsEnabled;
            appState.settings.notificationsEnabled = enabled;
            const knob = notificationToggle.querySelector('div');
            if (enabled) {
                notificationToggle.classList.add('bg-brand-600');
                notificationToggle.classList.remove('bg-slate-300');
                knob.classList.remove('left-1');
                knob.classList.add('left-7');
            } else {
                notificationToggle.classList.add('bg-slate-300');
                notificationToggle.classList.remove('bg-brand-600');
                knob.classList.remove('left-7');
                knob.classList.add('left-1');
            }
            saveSettings();
        });

        // Init
        loadSettings(); // Load from storage
        resetTimer();   // Initialize with loaded settings

        // If page visibility changes (user returns), recompute immediately
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) tick();
        });

        // rAF loop for smooth progress when visible; setInterval fallback handles backgrounded checks
        const rAFLoop = () => {
            if (appState.isRunning && !document.hidden && appState.endTimeMs) {
                // Light-weight update for progress bar and small visual smoothness
                const remainingMs = Math.max(0, appState.endTimeMs - Date.now());
                const remainingSec = Math.ceil(remainingMs / 1000);
                const pct = (remainingSec / appState.totalTime) * 100;
                els.progressBar.style.width = `${pct}%`;
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