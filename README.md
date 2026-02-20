# Training Log + Video Vault — Backend version (Flask)

This is the **backend** version you asked for:
- Coach + lifter accounts
- Shared database (comments persist across devices)
- High-quality media uploads from phone (videos/photos)
- Add/remove periods/blocks/weeks/days/exercises from the website

---

## Local setup (run on your computer)

### 1) Unzip and open a terminal in the folder

### 2) Create a virtual environment (recommended)
```bash
python -m venv .venv
# Windows:
# .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### 3) Install dependencies
```bash
pip install -r requirements.txt
```

### 4) Create a .env file
Copy `.env.example` to `.env` and edit values:
- SECRET_KEY (any random string)
- BOOTSTRAP_COACH_USER/PASS
- BOOTSTRAP_LIFTER_USER/PASS
- MAX_UPLOAD_MB (optional)

### 5) Run the server
```bash
python -m flask --app wsgi run --debug
```

Open:
- http://127.0.0.1:5000

Login with your bootstrap accounts.

---

## How the roles work

- **Coach**
  - Create/delete periods/blocks/weeks/days/exercises
  - Edit work + both comments
  - Delete media
- **Lifter**
  - Upload media
  - Write lifter comment
  - Read coach feedback

---

## Uploads + persistence (important!)

Uploads are stored on the server disk:
- Local dev: `instance/uploads/`
- Production: depends on host

If the host does **not** have persistent storage, uploaded videos will disappear on redeploy.
You want:
- Render: add a **Persistent Disk**
- Fly.io: add a **Volume**

---

## Deploy (recommended): Render.com

GitHub Pages cannot run Flask backends.

### 1) Put this project on GitHub
Create a repo, upload everything.

### 2) Create a Render Web Service
- New → Web Service
- Connect your repo
- Environment: Python
- Build command:
  `pip install -r requirements.txt`
- Start command:
  `gunicorn wsgi:app`

### 3) Add environment variables on Render
- SECRET_KEY
- BOOTSTRAP_COACH_USER / PASS
- BOOTSTRAP_LIFTER_USER / PASS
- MAX_UPLOAD_MB (optional)

### 4) Add a persistent disk (HIGHLY recommended)
- Add Disk
- Mount path: `/opt/render/project/src/instance`
  (this keeps your sqlite DB + uploads persistent)

### 5) Deploy and open the URL
Render provides a URL like:
- https://your-app.onrender.com

---

## Deploy (alternative): Fly.io (quick note)

You can run this on Fly with a volume for persistence.
If you want a Fly config generated, ask and I’ll provide it.

---

## Database notes

Default database is SQLite.
For heavier use, you can upgrade to Postgres later.

---

## Security notes (practical)
- Change bootstrap passwords after first login
- Keep SECRET_KEY secret
- Consider limiting upload size via MAX_UPLOAD_MB
