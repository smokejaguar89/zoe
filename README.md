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

You may need to run the following commands if lgpio fails:
```bash
sudo apt update
sudo apt install swig liblgpio-dev
```

## Configuration

Create `.env` in the project root:

```env
# Required for image generation
GEMINI_API_KEY=your_key_here

# Optional for local dev without sensors
SENSOR_MODE=TEST
```

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
  - use `SENSOR_MODE=TEST`
- Hardware import/platform errors:
  - confirm test mode is enabled before startup
- Gemini image generation not working:
  - verify `GEMINI_API_KEY` is set
