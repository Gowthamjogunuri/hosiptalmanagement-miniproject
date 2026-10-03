# Hospital Management System

## Local configuration

The application reads credentials from environment variables instead of storing them in source files. Set these before starting the app:

- `MYSQL_USER` and `MYSQL_PASSWORD` are required.
- `MYSQL_HOST`, `MYSQL_PORT`, and `MYSQL_DATABASE` are optional; they default to `127.0.0.1`, `3306`, and `redact`.
- `ADMIN_USERNAME` and `ADMIN_PASSWORD` are required for the application admin login.
- `DJANGO_SECRET_KEY` should be set to a unique secret outside local development. The development fallback is not suitable for deployment.

On Windows PowerShell, for example:

```powershell
$env:MYSQL_USER = "your-database-user"
$env:MYSQL_PASSWORD = "your-database-password"
$env:ADMIN_USERNAME = "your-admin-user"
$env:ADMIN_PASSWORD = "your-admin-password"
$env:DJANGO_SECRET_KEY = "your-django-secret"
python manage.py runserver
```

Local databases, identity-document/training inputs, uploaded reports and temporary images, screenshots, and notebook checkpoints are excluded from Git to avoid publishing personal data.
