# Hospital Management System

## Local configuration

The application reads credentials from environment variables instead of storing them in source files. Set these before starting the app:

- `MYSQL_USER` and `MYSQL_PASSWORD` are required.
- `MYSQL_HOST`, `MYSQL_PORT`, and `MYSQL_DATABASE` are optional; they default to `127.0.0.1`, `3306`, and `redact`.
- `ADMIN_USERNAME` and `ADMIN_PASSWORD` are required for the application admin login.
- `DJANGO_SECRET_KEY` should be set to a unique secret outside local development. The development fallback is not suitable for deployment.
- `MYSQL_SSL_CA` is optional; set it to the CA certificate file path when the MySQL provider requires TLS.

On Windows PowerShell, for example:

```powershell
$env:MYSQL_USER = "your-database-user"
$env:MYSQL_PASSWORD = "your-database-password"
$env:ADMIN_USERNAME = "your-admin-user"
$env:ADMIN_PASSWORD = "your-admin-password"
$env:DJANGO_SECRET_KEY = "your-django-secret"
python manage.py runserver
```

## Render demo deployment

This configuration is for a demonstration using fake patient data only. Do not upload real patient, Aadhaar, or medical records: the application does not have adequate authentication, authorization, or privacy safeguards for real health data.

1. Create a MySQL database named `redact` reachable from Render. Render's managed database offering is PostgreSQL, but this application uses MySQL directly.
2. Apply [`db.txt`](./db.txt) to that database. The script creates the tables if they do not exist and does not delete an existing database.
3. In Render, create a Blueprint from this GitHub repository and select `render.yaml`.
4. Add the database host, username, and password, plus unique demo-only admin credentials, when Render prompts for the `sync: false` environment variables. If your provider requires TLS, add a Render Secret File containing its CA certificate and set `MYSQL_SSL_CA` to that file's path.
5. Deploy. The Blueprint provisions a Docker service, a persistent disk for uploaded demo files, and a generated Django secret key. The disk and web service use paid Render plans.

The app uses the Blueprint's single `hospital-management-demo.onrender.com` host. If you rename the service or attach a custom domain, update `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` in Render to match it.

Local databases, identity-document/training inputs, uploaded reports and temporary images, screenshots, and notebook checkpoints are excluded from Git and the Docker build context.
