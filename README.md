# Zoe

_ζωή (zōē): life_

This is my pet project. It periodically takes readings from multiple sensors and
APIs, and based on this crafts a prompt to generate an image using nano banana.

The ultimate goal is to have an eink wall frame display these throughout the day.

## Project Layout

```text
app/
  api/                # API and HTML routes
  clients/            # External clients (Gemini)
  db/                 # Database layer
  hardware/           # Real and fake sensor drivers
  models/             # Domain, DTO, and DB entities
  scheduler/          # Background scheduler jobs
  services/           # Business logic
  static/             # JS and images
  templates/          # Jinja templates
tests/                # Test suite
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For Raspberry Pi / Linux hardware installs, also run:

```bash
pip install -r requirements-hardware.txt
```

`requirements.txt` is a lock file with every package pinned, so the Pi and
your laptop run the same versions. To add or upgrade a dependency, edit
`requirements.in` and regenerate the lock file with
[uv](https://docs.astral.sh/uv/) (add `--upgrade` to take new versions):

```bash
uv pip compile requirements.in --universal --python-version 3.10 -o requirements.txt
```

If `lgpio` fails on Pi, install system packages:
```bash
sudo apt update
sudo apt install swig liblgpio-dev
```

## Configuration

Settings are defined in `app/config.py`. Set them in a `.env` file in the
project root, or as environment variables (which take priority):

```env
# Required for image generation
GEMINI_API_KEY=your_key_here
NEWS_API_KEY=your_key_here

# Optional
GEMINI_MODEL=gemini-3.1-flash-image-preview
DATABASE_PATH=/path/to/sensors.db   # default: sensors.db in the project root
SENSOR_MODE=TEST                    # run with fake sensors, e.g. on a laptop
```

Paths are resolved from the project location, so the app can be started
from any directory.

## Run

Normal mode:

```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

TEST mode (no sensors connected):

```bash
SENSOR_MODE=TEST uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

App URL:

- http://localhost:8000

## API Endpoints

- `GET /`  
  Dashboard HTML page.
- `GET /api/sensors`  
  Current sensor snapshot.
- `GET /api/sensors/last_week_average`  
  Last-week average snapshot.
- `GET /api/sensors/time_series`  
  Last-week snapshots as time series.

## Database

- SQLite file path: `./sensors.db` (project root when started from repo root)
- Created automatically at startup

## Tests

```bash
pytest -q
```

## Troubleshooting

- Running on macOS/laptop without hardware:
  - install only `requirements.txt`
  - use `SENSOR_MODE=TEST`
- Hardware import/platform errors:
  - confirm test mode is enabled before startup
  - install `requirements-hardware.txt` only on the Linux device with sensors
- Gemini image generation not working:
  - verify `GEMINI_API_KEY` is set
