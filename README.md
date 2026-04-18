# **🔐 SecureGate — Next-Gen Apartment Visitor Security System**
**SecureGate** is an AI-powered, IoT-integrated backend system designed to prevent unauthorized access and spoofing in residential complexes. It combines real-time computer vision detection with a high-performance async API to ensure robust physical security.
## **🚀 Key Features**
- **Advanced Anti-Spoofing:** Integrates with AI Perception Modules to detect physical photos, video replays, and 3D masks.
- **Real-time Alert Routing:** Instantly alerts residents via WebSocket/Push notifications upon detecting fake or unknown entry attempts.
- **IoT Hardware Integration:** Ready to interface with edge devices (Raspberry Pi/GPIO) for automated gate unlocking upon successful verification.
- **Comprehensive Audit Trail:** Maintains immutable logs of all entry attempts, including spoof types and actionable outcomes, ensuring high accountability.
- **Privacy-First Design:** Built with minimal data retention principles, paving the way for DPDP Act and GDPR compliance.
## **🛠️ Tech Stack & Team Topology**
This project is a collaborative effort utilizing a multi-disciplinary tech stack:

- **Backend & Database (Faazil):** FastAPI, SQLite, Pydantic, Uvicorn
- **AI & Computer Vision (Mustafa):** OpenCV, FaceNet (External Module Integration)
- **IoT & Hardware (Shrushti):** Raspberry Pi, GPIO Event Triggers
- **Frontend Dashboard (Yasin):** HTML5, CSS3, Vanilla JS (Real-time DOM manipulation)
## **⚙️ Local Development Setup**
We highly recommend using a Virtual Environment to avoid global dependency conflicts.

**1. Clone the repository:**
```bash
git clone https://github.com/Drago1314/SecureGate.git
cd SecureGate
```

**2. Create & Activate Virtual Environment:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

**3. Run the Automated Startup Script:**
```bash
# For Windows
python start.py

# For Linux/Mac
bash start.sh
```

**4. Access the Platform:**

- **Interactive API Docs (Swagger UI):** http://localhost:8000/docs
- **Admin Dashboard:** Open `dashboard.html` in your browser.
## **📡 Core API Reference**
The backend exposes several RESTful endpoints. View the complete Swagger documentation at `/docs` for payload schemas.
### **🏠 Residents & Visitors**
- `POST /residents` - Register a new apartment resident.
- `GET /residents` - Fetch the resident directory.
- `POST /visitors` - Pre-register an expected visitor.
- `POST /visitors/{id}/photo` - Securely upload visitor biometric reference.
### **🛡️ AI Perception Engine Webhook**
The AI module calls this endpoint to log facial recognition results.

- `POST /entry`
```json
{
    "visitor_id": 3,
    "resident_id": 1,
    "status": "fake",
    "spoof_type": "photo",
    "snapshot_path": "snapshots/frame_xyz.jpg"
}
```
*Status Enum:* `verified` | `fake` | `unknown`  
*Spoof Enum:* `photo` | `video` | `mask` | `none`
### **🚨 Security Alerts & Metrics**
- `GET /alerts/{resident_id}` - Fetch active security alerts for a specific flat.
- `PATCH /alerts/{id}/read` - Acknowledge and dismiss an alert.
- `GET /stats` - Retrieve aggregate security metrics for the admin dashboard.
## **🔒 Security & Future Scope**
As a security-first application, our immediate roadmap includes:

1. **Database Encryption:** Migrating from standard SQLite to SQLCipher for encrypted at-rest data.
2. **JWT Authentication:** Securing API endpoints with short-lived access tokens.
3. **Blockchain Audit Logs:** Hashing entry logs into a private ledger to prevent post-incident tampering.

*Built with caffeine and chaos for QuantumHacks 2026.*
