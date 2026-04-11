from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3, os, shutil, uuid
from datetime import datetime

app = FastAPI(title="Apartment Visitor Security API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "visitor_security.db"
UPLOAD_DIR = "snapshots"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ─────────────────────────────────────────
# DB INIT
# ─────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS residents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            flat_number TEXT NOT NULL UNIQUE,
            name        TEXT NOT NULL,
            phone       TEXT NOT NULL,
            email       TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS visitors (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            phone           TEXT,
            photo_path      TEXT,
            registered_by   INTEGER REFERENCES residents(id),
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS entry_logs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            visitor_id      INTEGER REFERENCES visitors(id),
            resident_id     INTEGER REFERENCES residents(id),
            timestamp       TEXT DEFAULT (datetime('now')),
            status          TEXT CHECK(status IN ('verified','fake','unknown')) NOT NULL,
            spoof_type      TEXT CHECK(spoof_type IN ('photo','video','mask','none')) DEFAULT 'none',
            snapshot_path   TEXT,
            action_taken    TEXT CHECK(action_taken IN ('unlocked','denied','alerted')) NOT NULL
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_log_id    INTEGER REFERENCES entry_logs(id),
            resident_id     INTEGER REFERENCES residents(id),
            message         TEXT NOT NULL,
            sent_at         TEXT DEFAULT (datetime('now')),
            is_read         INTEGER DEFAULT 0
        );
    """)

    conn.commit()
    conn.close()

init_db()

# ─────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────
class ResidentCreate(BaseModel):
    flat_number: str
    name: str
    phone: str
    email: Optional[str] = None

class VisitorCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    registered_by: Optional[int] = None  # resident_id

class EntryResult(BaseModel):
    visitor_id: Optional[int] = None
    resident_id: Optional[int] = None
    status: str           # verified / fake / unknown
    spoof_type: str = "none"  # photo / video / mask / none
    snapshot_path: Optional[str] = None

# ─────────────────────────────────────────
# RESIDENTS
# ─────────────────────────────────────────
@app.post("/residents", status_code=201)
def add_resident(data: ResidentCreate):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO residents (flat_number, name, phone, email) VALUES (?,?,?,?)",
            (data.flat_number, data.name, data.phone, data.email)
        )
        conn.commit()
        return {"message": "Resident added successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Flat number already exists")
    finally:
        conn.close()

@app.get("/residents")
def get_residents():
    conn = get_db()
    rows = conn.execute("SELECT * FROM residents ORDER BY flat_number").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─────────────────────────────────────────
# VISITORS
# ─────────────────────────────────────────
@app.post("/visitors", status_code=201)
def add_visitor(data: VisitorCreate):
    conn = get_db()
    conn.execute(
        "INSERT INTO visitors (name, phone, registered_by) VALUES (?,?,?)",
        (data.name, data.phone, data.registered_by)
    )
    conn.commit()
    conn.close()
    return {"message": "Visitor registered"}

@app.post("/visitors/{visitor_id}/photo")
def upload_visitor_photo(visitor_id: int, file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1]
    filename = f"visitor_{visitor_id}_{uuid.uuid4().hex}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    conn = get_db()
    conn.execute("UPDATE visitors SET photo_path=? WHERE id=?", (path, visitor_id))
    conn.commit()
    conn.close()
    return {"photo_path": path}

@app.get("/visitors")
def get_visitors():
    conn = get_db()
    rows = conn.execute("SELECT * FROM visitors ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─────────────────────────────────────────
# ENTRY LOGS — main endpoint AI calls this
# ─────────────────────────────────────────
@app.post("/entry", status_code=201)
def log_entry(result: EntryResult):
    conn = get_db()

    # Decide action
    if result.status == "verified":
        action = "unlocked"
    elif result.status == "fake":
        action = "denied"
    else:
        action = "alerted"

    cur = conn.execute(
        """INSERT INTO entry_logs 
           (visitor_id, resident_id, status, spoof_type, snapshot_path, action_taken)
           VALUES (?,?,?,?,?,?)""",
        (result.visitor_id, result.resident_id,
         result.status, result.spoof_type,
         result.snapshot_path, action)
    )
    log_id = cur.lastrowid

    # Auto-alert resident if fake or unknown
    if result.status in ("fake", "unknown") and result.resident_id:
        msg = (
            f"⚠️ Fake entry attempt detected! Spoof type: {result.spoof_type}"
            if result.status == "fake"
            else "❓ Unknown visitor attempted entry. Please verify."
        )
        conn.execute(
            "INSERT INTO alerts (entry_log_id, resident_id, message) VALUES (?,?,?)",
            (log_id, result.resident_id, msg)
        )

    conn.commit()
    conn.close()

    return {"log_id": log_id, "action": action}

@app.get("/entry/logs")
def get_entry_logs(limit: int = 50):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM entry_logs ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─────────────────────────────────────────
# ALERTS
# ─────────────────────────────────────────
@app.get("/alerts/{resident_id}")
def get_alerts(resident_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM alerts WHERE resident_id=? ORDER BY sent_at DESC",
        (resident_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.patch("/alerts/{alert_id}/read")
def mark_alert_read(alert_id: int):
    conn = get_db()
    conn.execute("UPDATE alerts SET is_read=1 WHERE id=?", (alert_id,))
    conn.commit()
    conn.close()
    return {"message": "Alert marked as read"}

# ─────────────────────────────────────────
# STATS — for Yasin's dashboard
# ─────────────────────────────────────────
@app.get("/stats")
def get_stats():
    conn = get_db()
    total   = conn.execute("SELECT COUNT(*) FROM entry_logs").fetchone()[0]
    verified= conn.execute("SELECT COUNT(*) FROM entry_logs WHERE status='verified'").fetchone()[0]
    fake    = conn.execute("SELECT COUNT(*) FROM entry_logs WHERE status='fake'").fetchone()[0]
    unknown = conn.execute("SELECT COUNT(*) FROM entry_logs WHERE status='unknown'").fetchone()[0]
    conn.close()
    return {
        "total_entries": total,
        "verified": verified,
        "fake_attempts": fake,
        "unknown": unknown
    }
