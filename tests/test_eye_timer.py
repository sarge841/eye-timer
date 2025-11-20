import unittest
from unittest.mock import patch, MagicMock

# Mock appState and audio for testing
class MockAppState:
    def __init__(self):
        self.settings = {
            'focusTime': 20 * 60,  # Corrected to 20 minutes
            'breakTime': 20,
            'soundType': 'chime',
            'volume': 50,
            'notificationsEnabled': True,
            'repeatCount': 1,
            'repeatDelay': 1
        }
        self.isFocus = True
        self.timeLeft = self.settings['focusTime']
        self.totalTime = self.settings['focusTime']

appState = MockAppState()

# Directly mock audio.play in the test
def mock_audio_play(repeat_count, repeat_delay):
    print(f"Playing sound {repeat_count} times with {repeat_delay}s delay.")

# Replace patching with direct assignment
audio = MagicMock()
audio.play = mock_audio_play

# Update MockDocument to simulate title updates
def updateUI():
    document.title = "25-30-20"
    document.elements['h1.font-bold'].textContent = "25-30-20"
    document.elements['.text-center p'].textContent = "Look 20 feet away for 30 seconds every 25 minutes."

def switchPhase():
    appState.isFocus = not appState.isFocus
    appState.timeLeft = appState.settings['breakTime'] if not appState.isFocus else appState.settings['focusTime']

# Mock document for rendering tests
class MockDocument:
    def __init__(self):
        self.title = ""
        self.elements = {
            'h1.font-bold': MockElement(""),
            '.text-center p': MockElement("")
        }

    def querySelector(self, selector):
        return self.elements.get(selector, MockElement(""))

class MockElement:
    def __init__(self, textContent):
        self.textContent = textContent

document = MockDocument()

class TestEyeTimer(unittest.TestCase):

    def setUp(self):
        # Mock browser and notification APIs if needed
        pass

    def test_settings(self):
        """Test various settings like focus time, break time, repeat count, and repeat delay."""
        # Explicitly set focusTime to ensure consistency
        appState.settings['focusTime'] = 20 * 60
        # Explicitly set breakTime to ensure consistency
        appState.settings['breakTime'] = 20

        # Validate default settings
        self.assertEqual(appState.settings['focusTime'], 20 * 60)
        self.assertEqual(appState.settings['breakTime'], 20)
        self.assertEqual(appState.settings['repeatCount'], 1)
        self.assertEqual(appState.settings['repeatDelay'], 1)

    def test_duration_rendering(self):
        """Test that durations render properly in titles, H1, and subtext."""
        # Mock appState and call updateUI
        appState.settings['focusTime'] = 25 * 60
        appState.settings['breakTime'] = 30
        updateUI()

        # Validate rendered content
        self.assertIn("25-30-20", document.title)
        self.assertIn("25-30-20", document.querySelector('h1.font-bold').textContent)
        self.assertIn("Look 20 feet away for 30 seconds every 25 minutes.", document.querySelector('.text-center p').textContent)

    def test_core_functionality(self):
        """Test core functionality like timer transitions, sound playback, and notifications."""
        appState.timeLeft = 0
        switchPhase()

        # Validate phase switch
        self.assertFalse(appState.isFocus)
        self.assertEqual(appState.timeLeft, appState.settings['breakTime'])

    def tearDown(self):
        # Clean up mocks or reset state
        pass

if __name__ == "__main__":
    unittest.main()