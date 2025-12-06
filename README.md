# ServeLoop — Track, Verify, and Celebrate Real-World Social Impact

A lightweight Streamlit MVP for organizing, verifying, and gamifying volunteer impact.

---

## Quick features

* Create and discover social impact events (environment, health, education, community).
* QR-based check-in and proof upload (images/videos).
* Organizer verification panel to validate contributions.
* Gamified ServePass with badges and shareable profile.
* Lightweight local SQLite DB with optional Cloudinary media storage and AI tagging fallbacks.

---


## Setup 

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.\.venv\Scripts\activate  # Windows PowerShell
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment variables from `.env.example` into a local `.env` (or set them in your shell). For a quick demo you can skip Cloudinary and AI provider variables — the app has local fallbacks.

4. Initialize the database and seed demo data (optional):

```bash
python -c "from database.models import init_db, seed_demo_data; init_db(); seed_demo_data()"
```

5. Run the app:

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser (or use the Streamlit Cloud link if deployed).

---

## Optional: Cloud media uploads

To upload and serve images/videos from Cloudinary, set the following in your `.env`:

```
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-secret
```

The app uses `utils/cloudinary_utils.py` when these values are present; otherwise it falls back to data-URLs for demo purposes.

---

