# Deployment Guide for Grocery App

## Render Deployment Setup

### 1. Environment Variables
Set these environment variables in your Render dashboard:

- `DEBUG`: `False`
- `SECRET_KEY`: Generate a new secret key (you can use Django's `python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- `DATABASE_URL`: Render will provide this automatically when you create a PostgreSQL database

### 2. Build Configuration
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn Grocery.wsgi:application`

### 3. Admin Access
After deployment, you can access the admin panel at:
`https://your-app-name.onrender.com/admin/`

**Default Admin Credentials:**
- Username: `admin`
- Password: `admin123`
- Email: `admin@example.com`

### 4. Troubleshooting

#### If you can't login to admin:
1. Check that the build script ran successfully
2. Verify environment variables are set correctly
3. Check the deployment logs for any errors
4. You can create a new superuser manually by running:
   ```bash
   python manage.py create_superuser
   ```

#### If the app doesn't start:
1. Check that all dependencies are in `requirements.txt`
2. Verify the start command is correct
3. Check the build logs for any errors

### 5. Security Notes
- Change the default admin password after first login
- Consider using environment variables for sensitive data
- Enable HTTPS (Render does this automatically)
- Keep DEBUG=False in production 