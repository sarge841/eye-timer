import importlib.util
import json
import os
import re
import unittest
from unittest.mock import patch, MagicMock


VALID_BURN_IN_MODES = ('drift', 'bounce', 'aurora', 'starfield')


class MockAppState:
    def __init__(self):
        self.settings = {
            'focusTime': 20 * 60,
            'breakTime': 20,
            'soundType': 'chime',
            'volume': 50,
            'notificationsEnabled': True,
            'reverseOnBreakEnd': False,
            'repeatCount': 1,
            'repeatDelay': 1,
            'burnInEnabled': False,
            'burnInMode': 'drift',
        }
        self.isFocus = True
        self.timeLeft = self.settings['focusTime']
        self.totalTime = self.settings['focusTime']


class TestEyeTimer(unittest.TestCase):
    def setUp(self):
        self.appState = MockAppState()

    def test_default_settings_include_reverse(self):
        """Ensure the new reverseOnBreakEnd setting exists and defaults to False."""
        self.assertIn('reverseOnBreakEnd', self.appState.settings)
        self.assertFalse(self.appState.settings['reverseOnBreakEnd'])

    def test_default_settings_include_burn_in(self):
        """Ensure burnInEnabled and burnInMode exist with expected defaults."""
        self.assertIn('burnInEnabled', self.appState.settings)
        self.assertFalse(self.appState.settings['burnInEnabled'])
        self.assertIn('burnInMode', self.appState.settings)
        self.assertEqual(self.appState.settings['burnInMode'], 'drift')

    def test_toggle_reverse_setting(self):
        """Toggling the reverse setting changes the stored value."""
        self.appState.settings['reverseOnBreakEnd'] = True
        self.assertTrue(self.appState.settings['reverseOnBreakEnd'])

    def test_toggle_burn_in_and_modes(self):
        """Toggling burn-in protection and cycling through all supported modes works."""
        self.appState.settings['burnInEnabled'] = True
        self.assertTrue(self.appState.settings['burnInEnabled'])

        for mode in VALID_BURN_IN_MODES:
            self.appState.settings['burnInMode'] = mode
            self.assertEqual(self.appState.settings['burnInMode'], mode)

    def test_phase_switch_updates_state(self):
        """Simple phase switch flips focus state and updates timeLeft appropriately."""
        # Simulate end of focus
        self.appState.isFocus = True
        # switch to break
        self.appState.isFocus = not self.appState.isFocus
        if not self.appState.isFocus:
            self.appState.timeLeft = self.appState.settings['breakTime']
        self.assertFalse(self.appState.isFocus)
        self.assertEqual(self.appState.timeLeft, self.appState.settings['breakTime'])

    def test_audio_play_reverse_flag(self):
        """When transitioning into focus (break ended) and reverse is enabled, audio.play receives reverse=True."""
        app = MockAppState()
        app.settings['reverseOnBreakEnd'] = True
        app.settings['repeatCount'] = 2
        app.settings['repeatDelay'] = 3

        # Case A: currently on break, so next phase is focus -> reverse should be True
        app.isFocus = False
        calls = []

        class MockAudio:
            def play(self, repeatCount, repeatDelay, reverse=False):
                calls.append((int(repeatCount), int(repeatDelay), bool(reverse)))

        audio = MockAudio()
        nextIsFocus = not app.isFocus
        reverseFlag = nextIsFocus and app.settings['reverseOnBreakEnd']
        audio.play(app.settings['repeatCount'], app.settings['repeatDelay'], reverseFlag)
        self.assertEqual(calls, [(2, 3, True)])

        # Case B: currently on focus, so next phase is break -> reverse should be False even if enabled
        app.isFocus = True
        calls.clear()
        nextIsFocus = not app.isFocus
        reverseFlag = nextIsFocus and app.settings['reverseOnBreakEnd']
        audio.play(app.settings['repeatCount'], app.settings['repeatDelay'], reverseFlag)
        self.assertEqual(calls, [(2, 3, False)])

    def test_settings_serialization_roundtrip(self):
        """Settings including reverseOnBreakEnd and burnIn settings serialize/deserialize cleanly to JSON."""
        s = self.appState.settings
        s['reverseOnBreakEnd'] = True
        s['repeatCount'] = 4
        s['repeatDelay'] = 2
        s['burnInEnabled'] = True
        s['burnInMode'] = 'aurora'

        blob = json.dumps(s)
        loaded = json.loads(blob)

        # JSON roundtrip should preserve keys and values (booleans become booleans)
        self.assertIn('reverseOnBreakEnd', loaded)
        self.assertTrue(loaded['reverseOnBreakEnd'])
        self.assertEqual(int(loaded['repeatCount']), 4)
        self.assertEqual(int(loaded['repeatDelay']), 2)
        self.assertTrue(loaded['burnInEnabled'])
        self.assertEqual(loaded['burnInMode'], 'aurora')

    def _mimic_load_settings(self, saved_blob, app):
        """Mimic the JS loadSettings mapping into appState.settings.

        The frontend saves some fields as strings (focus minutes, break seconds,
        repeat counts/delays). This helper parses those and applies to the
        provided app object's settings dict similar to the JS logic.
        """
        data = json.loads(saved_blob)

        if 'focus' in data:
            try:
                app.settings['focusTime'] = int(data['focus']) * 60
            except Exception:
                pass

        if 'break' in data:
            try:
                app.settings['breakTime'] = int(data['break'])
            except Exception:
                pass

        if 'sound' in data:
            app.settings['soundType'] = data['sound']

        if 'volume' in data:
            try:
                app.settings['volume'] = int(data['volume'])
            except Exception:
                pass

        if 'repeatCount' in data:
            try:
                app.settings['repeatCount'] = int(data['repeatCount'])
            except Exception:
                pass

        if 'repeatDelay' in data:
            try:
                app.settings['repeatDelay'] = int(data['repeatDelay'])
            except Exception:
                pass

        if 'notificationsEnabled' in data:
            # JS used nullish coalescing; treat explicit boolean values
            app.settings['notificationsEnabled'] = bool(data['notificationsEnabled'])

        if 'reverse' in data:
            app.settings['reverseOnBreakEnd'] = bool(data['reverse'])

        if 'burnInEnabled' in data:
            app.settings['burnInEnabled'] = bool(data['burnInEnabled'])

        if 'burnInMode' in data and data['burnInMode'] in VALID_BURN_IN_MODES:
            app.settings['burnInMode'] = data['burnInMode']

        # Theme is not part of app settings in the Python model; ignore

        return app

    def test_persistence_load_mapping(self):
        """Simulate saved localStorage blob and ensure fields map into settings."""
        saved = {
            'focus': '15',
            'break': '25',
            'sound': 'harp',
            'volume': '80',
            'repeatCount': '3',
            'repeatDelay': '2',
            'theme': 'dark',
            'notificationsEnabled': False,
            'reverse': True,
            'burnInEnabled': True,
            'burnInMode': 'bounce',
        }
        blob = json.dumps(saved)
        app = MockAppState()
        self._mimic_load_settings(blob, app)

        self.assertEqual(app.settings['focusTime'], 15 * 60)
        self.assertEqual(app.settings['breakTime'], 25)
        self.assertEqual(app.settings['soundType'], 'harp')
        self.assertEqual(app.settings['volume'], 80)
        self.assertEqual(app.settings['repeatCount'], 3)
        self.assertEqual(app.settings['repeatDelay'], 2)
        self.assertFalse(app.settings['notificationsEnabled'])
        self.assertTrue(app.settings['reverseOnBreakEnd'])
        self.assertTrue(app.settings['burnInEnabled'])
        self.assertEqual(app.settings['burnInMode'], 'bounce')

    def test_invalid_burn_in_mode_ignored_on_load(self):
        """Invalid burnInMode values fall back to existing valid mode."""
        saved = {
            'burnInEnabled': True,
            'burnInMode': 'invalid-mode',
        }
        blob = json.dumps(saved)
        app = MockAppState()
        self._mimic_load_settings(blob, app)
        self.assertTrue(app.settings['burnInEnabled'])
        self.assertEqual(app.settings['burnInMode'], 'drift')

    def test_persistence_missing_fields_do_not_clobber(self):
        """When saved blob lacks keys, existing settings are preserved."""
        partial = {'focus': '10'}
        blob = json.dumps(partial)
        app = MockAppState()
        # mutate one to detect preservation
        app.settings['soundType'] = 'digital'
        app.settings['burnInMode'] = 'starfield'
        self._mimic_load_settings(blob, app)

        self.assertEqual(app.settings['focusTime'], 10 * 60)
        # unchanged values remain
        self.assertEqual(app.settings['soundType'], 'digital')
        self.assertEqual(app.settings['burnInMode'], 'starfield')


class TestFlaskAppFrontend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_path = os.path.join(repo_root, 'eye-timer.py')
        spec = importlib.util.spec_from_file_location('eye_timer', script_path)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.client = cls.module.app.test_client()

    def test_index_route_renders(self):
        """GET / returns 200 and renders the HTML application."""
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn('20-20-20 Eye Timer', html)

    def test_fullscreen_button_next_to_settings_icon(self):
        """Ensure fullscreen toggle button with expand icon sits right next to settings button."""
        html = self.client.get('/').get_data(as_text=True)
        self.assertIn('id="toggle-fullscreen"', html)
        self.assertIn('id="fullscreen-icon"', html)
        self.assertIn('fa-expand', html)
        self.assertIn('fa-compress', html)
        # Verify toggle-fullscreen appears immediately before open-settings inside the header action container
        pattern = re.compile(
            r'id="toggle-fullscreen".*?id="fullscreen-icon".*?</button>\s*<button[^>]*id="open-settings"',
            re.DOTALL,
        )
        self.assertRegex(html, pattern)

    def test_burn_in_settings_and_modes_present(self):
        """Ensure dynamic anti-burn-in toggle, mode selector, and all 4 modes exist in HTML."""
        html = self.client.get('/').get_data(as_text=True)
        self.assertIn('id="burn-in-toggle"', html)
        self.assertIn('id="burn-in-mode"', html)
        for mode in VALID_BURN_IN_MODES:
            self.assertIn(f'<option value="{mode}">', html)
        # Check dark mode and light mode handling in dynamic screen
        self.assertIn('html.dark body.burn-in-active', html)
        self.assertIn('html:not(.dark) body.burn-in-active', html)
        self.assertIn('BOUNCE_PALETTES', html)
        self.assertIn('stepBurnInAnimation', html)

    def test_favicon_route(self):
        """GET /favicon.png returns 200."""
        resp = self.client.get('/favicon.png')
        self.assertEqual(resp.status_code, 200)
        resp.close()


if __name__ == '__main__':
    unittest.main()
