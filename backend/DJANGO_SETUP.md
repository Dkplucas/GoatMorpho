# Django Backend Setup Guide

This guide will help you set up the Django backend for GoatMeasure Pro.

## Prerequisites

- Python 3.9 or higher
- PostgreSQL (optional, SQLite is default)
- Redis (optional, for Celery background tasks)

## Installation Steps

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` file with your settings:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/goatmeasure
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 4. Database Setup

Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

Create a superuser:

```bash
python manage.py createsuperuser
```

### 5. Static Files

Collect static files (for production):

```bash
python manage.py collectstatic
```

## Running the Server

### Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

### Production Server

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn goat_measure.wsgi:application --bind 0.0.0.0:8000
```

## Background Tasks (Optional)

If you want to use Celery for background image processing:

### 1. Install and Start Redis

```bash
# On Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis

# On macOS
brew install redis
brew services start redis
```

### 2. Start Celery Worker

```bash
celery -A goat_measure worker --loglevel=info
```

### 3. Start Celery Beat (for scheduled tasks)

```bash
celery -A goat_measure beat --loglevel=info
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/profile/` - Get user profile

### Measurements
- `GET /api/measurements/` - List measurements
- `POST /api/measurements/` - Upload image for analysis
- `GET /api/measurements/{id}/` - Get specific measurement
- `DELETE /api/measurements/{id}/` - Delete measurement
- `GET /api/measurements/{id}/download_csv/` - Download CSV results
- `GET /api/measurements/statistics/` - Get user statistics

## Admin Interface

Access the Django admin at `http://localhost:8000/admin/` with your superuser credentials.

## Testing

Run tests:

```bash
python manage.py test
```

## Database Schema

The main models are:

### User Model
- Extended Django User model with email field
- Stores user authentication and profile information

### Measurement Model
- Stores uploaded images and morphometric measurements
- 17 different measurement fields for comprehensive analysis
- Processing status tracking
- Confidence scores and metadata

## File Structure

```
backend/
├── goat_measure/          # Django project settings
├── authentication/        # User authentication app
├── measurements/          # Measurement processing app
├── media/                # Uploaded files
├── static/               # Static files
├── requirements.txt      # Python dependencies
└── manage.py            # Django management script
```

## Security Considerations

1. **Secret Key**: Generate a strong secret key for production
2. **Database**: Use PostgreSQL for production
3. **CORS**: Configure CORS settings for your frontend domain
4. **File Uploads**: Implement proper file validation and size limits
5. **Rate Limiting**: Consider implementing rate limiting for API endpoints

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL in .env file
   - Ensure PostgreSQL is running
   - Verify database credentials

2. **CORS Errors**
   - Check CORS_ALLOWED_ORIGINS in settings
   - Ensure frontend URL is included

3. **File Upload Errors**
   - Check MEDIA_ROOT permissions
   - Verify file size limits
   - Ensure Pillow is installed for image processing

4. **Celery Tasks Not Running**
   - Check Redis connection
   - Verify Celery worker is running
   - Check task queue in Redis

## Production Deployment

For production deployment:

1. Set `DEBUG=False`
2. Use a production database (PostgreSQL)
3. Configure proper static file serving
4. Set up proper logging
5. Use environment variables for sensitive settings
6. Configure SSL/TLS
7. Set up monitoring and error tracking

## Support

For issues and questions:
1. Check the Django documentation
2. Review the API documentation
3. Check the GitHub issues
4. Contact support team