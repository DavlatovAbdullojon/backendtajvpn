# TAJ VPN Backend

FastAPI backend for the Flutter Android VPN app. The backend identifies users by `deviceId`, accepts receipt uploads, grants provisional VPN access immediately, sends the receipt to the owner by email, and provides simple admin endpoints for approve, reject, ban, and unban actions.

## Features

- No registration and no login
- `deviceId` based user identity
- SQLite storage for local start
- Multipart receipt upload
- SMTP email notification with receipt attachment
- Provisional access after upload
- Admin actions to approve, reject, ban, and unban
- Static `/servers` endpoint scaffold for Flutter

## Project Structure

```text
backend/
  config.py
  database.py
  main.py
  models.py
  schemas.py
  requirements.txt
  .env.example
  routers/
    admin.py
    device.py
    plans.py
    receipts.py
    servers.py
    subscription.py
  services/
    device_service.py
    email_service.py
    receipt_service.py
    seed_service.py
    server_service.py
    subscription_service.py
  uploads/
```

## Access Status Logic

- `inactive`: user has no active access
- `provisional`: receipt was uploaded, email was sent through backend, access is enabled immediately
- `active`: admin approved the receipt
- `rejected`: admin rejected the receipt, access is disabled
- `banned`: device was banned, access is disabled immediately

VPN access is allowed only for `provisional` and `active`.

## API Endpoints

- `POST /device/init`
- `GET /plans`
- `POST /receipts/upload`
- `GET /subscription/status?deviceId=...`
- `GET /servers`
- `GET /admin/receipts`
- `POST /admin/receipts/{id}/approve`
- `POST /admin/receipts/{id}/reject`
- `POST /admin/users/{deviceId}/ban`
- `POST /admin/users/{deviceId}/unban`

## Local Run

### 1. Create a virtual environment

```bash
cd backend
python -m venv .venv
```

### 2. Activate it

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create `.env`

Copy `.env.example` to `.env` and change these values:

- `ADMIN_EMAIL`: where receipt emails will be sent
- `MAIL_FROM`: sender email address
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_USE_TLS` or `SMTP_USE_SSL`
- `PUBLIC_BASE_URL`: public host for uploaded receipt links

### 5. Start the server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## Default Tariff Plans

The backend seeds two plans on startup:

- `month_1`: 100 RUB / 30 days
- `months_3`: 250 RUB / 90 days

If you want to change prices or duration, edit `services/seed_service.py`.

## Receipt Upload Contract

`POST /receipts/upload` expects `multipart/form-data`:

- `deviceId`
- `planId`
- `amountRub`
- `submittedAt` optional ISO datetime
- `platform` optional, default `android`
- `appVersion` optional
- `deviceModel` optional
- `notes` optional
- `receipt` file

After upload:

1. The receipt file is saved locally in `uploads/`
2. The backend stores the receipt row
3. The user subscription becomes `provisional`
4. VPN access becomes available immediately
5. The backend sends an email with the receipt attachment to `ADMIN_EMAIL`

## Admin Flow

### Approve

`POST /admin/receipts/{id}/approve`

- receipt status becomes `approved`
- subscription status becomes `active`

### Reject

`POST /admin/receipts/{id}/reject`

- receipt status becomes `rejected`
- subscription status becomes `rejected`
- VPN access is disabled

### Ban

`POST /admin/users/{deviceId}/ban`

- user status becomes `banned`
- VPN access is disabled immediately

### Unban

`POST /admin/users/{deviceId}/unban`

- backend recalculates access from the latest receipt
- if the latest valid receipt is approved and not expired, user returns to `active`
- if the latest receipt is still pending and not expired, user returns to `provisional`
- otherwise the user becomes `inactive`

## Integration Points For Flutter

- `POST /device/init`: call once on first app start or after reinstall
- `GET /plans`: fetch tariffs for the plans screen
- `POST /receipts/upload`: send receipt file after manual payment
- `GET /subscription/status`: gate the VPN connect button
- `GET /servers`: fill the server picker

## Deployment

### Simple Linux VPS deployment

1. Install Python 3.11+ and `nginx`
2. Copy the `backend/` folder to the server
3. Create `.env`
4. Create a virtual environment and install requirements
5. Run:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

6. Put `nginx` in front of it and proxy `/` to `127.0.0.1:8000`
7. Expose `/uploads` only if you want direct receipt file links from the admin list

### systemd example

`/etc/systemd/system/taj-vpn-backend.service`

```ini
[Unit]
Description=TAJ VPN Backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/taj-vpn/backend
EnvironmentFile=/opt/taj-vpn/backend/.env
ExecStart=/opt/taj-vpn/backend/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable taj-vpn-backend
sudo systemctl start taj-vpn-backend
```

## Production Notes

- Add admin authentication before exposing `/admin/*` publicly
- Replace SQLite with PostgreSQL for production load
- Move receipt files to object storage if you need backups and scaling
- Add audit logs for approve, reject, ban, and unban actions
- Add antivirus scanning for uploaded files
- Add HTTPS and rate limiting in front of the API
