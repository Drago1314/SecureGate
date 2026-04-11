# 🔐 Apartment Visitor Security — Backend

## Setup

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs (Swagger auto-generated ✅)

---

## Endpoints

### Residents
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/residents` | Add new resident |
| GET | `/residents` | List all residents |

### Visitors
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/visitors` | Register visitor |
| POST | `/visitors/{id}/photo` | Upload visitor photo |
| GET | `/visitors` | List all visitors |

### Entry (AI calls this)
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/entry` | Log entry result from AI module |
| GET | `/entry/logs` | Get recent entry logs |

### Alerts
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/alerts/{resident_id}` | Get alerts for resident |
| PATCH | `/alerts/{id}/read` | Mark alert as read |

### Stats (Dashboard)
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/stats` | Total / verified / fake / unknown counts |

---

## How AI module (Mustafa) calls this

```python
import requests

payload = {
    "visitor_id": 3,         # None if unknown
    "resident_id": 1,
    "status": "fake",        # verified / fake / unknown
    "spoof_type": "photo",   # photo / video / mask / none
    "snapshot_path": "snapshots/frame_xyz.jpg"
}

response = requests.post("http://localhost:8000/entry", json=payload)
print(response.json())  # {"log_id": 12, "action": "denied"}
```

---

## DB
- SQLite file: `visitor_security.db` (auto-created on first run)
- No setup needed 🔥
