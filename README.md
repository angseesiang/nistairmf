# NIST AI RMF Portal (Flask)

A simple role-based web application for NIST AI Risk Management Framework workflows:

- **Admin** can create/edit/disable/enable/delete users and create additional admins.
- **User** can log in and submit status-update prompts.
- Prompts are captured and mapped to NIST AI RMF functions (`GOVERN`, `MAP`, `MEASURE`, `MANAGE`, `UNMAPPED`).

## Step-by-step setup on Ubuntu

### 1) Update Ubuntu packages
```bash
sudo apt update
sudo apt upgrade -y
```

### 2) Install Python and venv tools
```bash
sudo apt install -y python3 python3-venv python3-pip
```

### 3) Download or copy this project
If using git:
```bash
git clone <your-repo-url> nistairmf
cd nistairmf
```

### 4) Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 5) Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6) Run the application
```bash
python app.py
```

The app will start on:
- `http://127.0.0.1:5000`

### 7) Log in with the default admin account
On first run, the app seeds an admin account:
- **Username:** `admin`
- **Password:** `admin123`

### 8) Create user/admin accounts
1. Log in as admin.
2. Open **Manage Users**.
3. Create users and set role (`user` or `admin`).
4. Use actions to edit, disable/enable, or delete users.

### 9) Submit user status prompts
1. Log in as a `user` account.
2. On dashboard, submit a prompt in **Status Update Chat**.
3. The app stores:
   - original prompt,
   - mapped NIST function,
   - generated status message.

---

## Optional: run as a background service (systemd)

Create service file:
```bash
sudo nano /etc/systemd/system/nistairmf.service
```

Paste (update `User` and paths):
```ini
[Unit]
Description=NIST AI RMF Flask App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/nistairmf
Environment="PATH=/home/ubuntu/nistairmf/.venv/bin"
ExecStart=/home/ubuntu/nistairmf/.venv/bin/python /home/ubuntu/nistairmf/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable nistairmf
sudo systemctl start nistairmf
sudo systemctl status nistairmf
```

---

## Notes
- For production, change `SECRET_KEY` in `app.py`.
- For production, disable debug mode and use Gunicorn + Nginx.
- Replace default admin password immediately after first login.

