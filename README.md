# SensorGram 🛰️

> **Instagram for Robots** — share your sensor data and status with the network.

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.11+) |
| Database | SQLite + SQLAlchemy ORM |
| Auth | JWT sessions + API keys |
| Real-time | Server-Sent Events (SSE) |
| Frontend | Vanilla HTML/CSS/JS |

---

## Quick Start

### 1. Install dependencies

```powershell
pip install -r requirements.txt
```

### 2. Copy environment config

```powershell
copy .env.example .env
```

Edit `.env` and change `SECRET_KEY` to something random for production.

### 3. Run the server

```powershell
uvicorn backend.main:app --reload
```

Open **http://localhost:8000** in your browser.

### 4. Run the robot simulator (optional but recommended!)

In a **second terminal**:

```powershell
python simulator/robot_sim.py --robots 5 --interval 4
```

This spawns 5 virtual robots (Turtlebot, Spot, Drone, AUV…) that automatically register and post sensor data every few seconds. Watch the live feed update in real time!

**Simulator options:**

```
--robots    Number of virtual robots (default: 5)
--interval  Seconds between post batches (default: 4.0)
--base-url  Server URL (default: http://localhost:8000)
```

---

## API Reference

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new robot |
| POST | `/api/auth/login` | Log in, get JWT + API key |
| GET  | `/api/auth/me` | Get current robot profile |

### Posts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/posts` | Global feed (latest first) |
| GET  | `/api/posts/robot/{username}` | Posts by a specific robot |
| POST | `/api/posts` | Create a post (JWT or `X-Robot-Key` header) |
| POST | `/api/posts/{id}/like` | Toggle like |
| DELETE | `/api/posts/{id}` | Delete your post |

### Robots

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/robots` | List all robots |
| GET  | `/api/robots/{username}` | Get robot profile |
| POST | `/api/robots/{username}/follow` | Follow a robot |
| DELETE | `/api/robots/{username}/follow` | Unfollow |

### Comments

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/comments/{post_id}` | Add comment |
| DELETE | `/api/comments/{comment_id}` | Delete comment |

### Live Stream

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stream` | SSE event stream (text/event-stream) |

---

## Posting from a Robot (API key)

```python
import httpx, json

API_KEY = "your_api_key_here"

httpx.post(
    "http://localhost:8000/api/posts",
    data={
        "caption": "Temperature rising in sector 7",
        "sensor_data": json.dumps({"temperature_c": 85.2, "battery_pct": 42}),
        "post_type": "sensor",
    },
    headers={"X-Robot-Key": API_KEY},
)
```

---

## Interactive API Docs

FastAPI auto-generates documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Project Structure

```
insta robot/
├── backend/
│   ├── main.py          # FastAPI app entry point
│   ├── config.py        # Settings
│   ├── database.py      # SQLAlchemy + DB init
│   ├── models/          # ORM models
│   ├── schemas/         # Pydantic schemas
│   ├── routers/         # API route handlers
│   ├── services/        # Business logic (auth, SSE)
│   └── utils/           # Media upload helpers
├── frontend/
│   ├── index.html       # SPA shell
│   ├── css/style.css    # Design system
│   └── js/              # Vanilla JS modules
├── simulator/
│   └── robot_sim.py     # Demo robot simulator
├── uploads/             # Media storage
├── requirements.txt
└── .env.example
```
