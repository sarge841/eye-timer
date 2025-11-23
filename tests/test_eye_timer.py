import unittest
from unittest.mock import patch, MagicMock

# Mock appState and audio for testing
import json


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
            'repeatDelay': 1
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

    def test_toggle_reverse_setting(self):
        """Toggling the reverse setting changes the stored value."""
        self.appState.settings['reverseOnBreakEnd'] = True
        self.assertTrue(self.appState.settings['reverseOnBreakEnd'])

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
        """Settings including reverseOnBreakEnd should serialize/deserialize cleanly to JSON."""
        s = self.appState.settings
        s['reverseOnBreakEnd'] = True
        s['repeatCount'] = 4
        s['repeatDelay'] = 2

        blob = json.dumps(s)
        loaded = json.loads(blob)

        # JSON roundtrip should preserve keys and values (booleans become booleans)
        self.assertIn('reverseOnBreakEnd', loaded)
        self.assertTrue(loaded['reverseOnBreakEnd'])
        self.assertEqual(int(loaded['repeatCount']), 4)
        self.assertEqual(int(loaded['repeatDelay']), 2)

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
            'reverse': True
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

    def test_persistence_missing_fields_do_not_clobber(self):
        """When saved blob lacks keys, existing settings are preserved."""
        partial = {'focus': '10'}
        blob = json.dumps(partial)
        app = MockAppState()
        # mutate one to detect preservation
        app.settings['soundType'] = 'digital'
        self._mimic_load_settings(blob, app)

        self.assertEqual(app.settings['focusTime'], 10 * 60)
        # unchanged values remain
        self.assertEqual(app.settings['soundType'], 'digital')


if __name__ == '__main__':
    unittest.main()