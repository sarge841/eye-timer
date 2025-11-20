# Eye Timer

Eye Timer is a productivity timer application designed to help users maintain focus and take regular breaks. It includes customizable settings for focus time, break time, and notification sounds.

## Disclaimer
This application was built entirely using AI tools and assistance. While every effort has been made to ensure its functionality and reliability, users are encouraged to review the code and adapt it to their specific needs.

## Features
- Customizable focus and break durations.
- Audio notifications with adjustable repeat count and delay.
- Dark mode and notification toggles.
- Simple and intuitive user interface.

## Prerequisites
- Python 3.8 or higher
- `uv` installed for running the app and tests
- Virtual environment (recommended)

## Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd eye-timer
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application
To start the application, use the `uv` command:
```bash
uv run eye-timer.py
```
This will launch the application, and you can access it in your browser.

## Running Tests
To run the test suite, use the following command:
```bash
uv run tests/test_eye_timer.py
```
This will execute all the unit tests and display the results.

## How `uv` is Used
- `uv` is used to run the application and test scripts seamlessly.
- It ensures the correct Python environment is used and simplifies execution commands.

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
This project is licensed under the MIT License. See the LICENSE file for details.