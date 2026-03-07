# Quick Start Guide

This guide will help you get the Document Processing Platform up and running quickly.

## Prerequisites

Before you begin, make sure you have the following installed:

- **Python 3.9+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **Git**

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd document-processing-platform
```

### 2. Run the Setup Script

```bash
python setup.py
```

This script will:
- Check system requirements
- Set up the backend Python environment
- Set up the frontend Node.js environment
- Start the database services
- Create environment configuration files

### 3. Configure Environment

Copy the example environment file and update it with your settings:

```bash
cp .env.example .env
```

Edit the `.env` file and update the following key settings:
- `SECRET_KEY`: Generate a secure random key
- `DATABASE_URL`: Update if using different database credentials
- `REDIS_URL`: Update if using different Redis configuration

### 4. Start the Application

```bash
docker-compose up -d
```

This will start all services:
- **Backend API** (FastAPI) on port 8000
- **Frontend** (React) on port 3000
- **PostgreSQL** database on port 5432
- **Redis** cache on port 6379
- **Celery Worker** for background processing
- **Flower** monitoring on port 5555

## Accessing the Application

### Web Interface
- **Main Application**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc
- **Celery Monitoring**: http://localhost:5555

### API Endpoints
- **Health Check**: http://localhost:8000/health
- **API Base**: http://localhost:8000/api/v1

## First Steps

### 1. Create an Account
1. Navigate to http://localhost:3000
2. Click "Register" to create a new account
3. Fill in your details and create the account

### 2. Upload Your First Document
1. Log in to your account
2. Click "Upload Document" or drag and drop a file
3. Supported formats: PDF, JPEG, PNG, TIFF
4. The system will automatically process the document

### 3. View Processing Results
1. Navigate to "Documents" to see your uploaded files
2. Click on a document to view processing results
3. View extracted text, entities, and analysis

## Development

### Backend Development
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn api.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm start
```

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running: `docker-compose ps`
   - Check database credentials in `.env`
   - Restart services: `docker-compose restart`

2. **OCR Not Working**
   - Ensure Tesseract is installed in the Docker container
   - Check OCR configuration in settings
   - Verify document format is supported

3. **Frontend Not Loading**
   - Check if React app is running on port 3000
   - Verify API URL configuration
   - Check browser console for errors

4. **Processing Jobs Not Running**
   - Ensure Celery worker is running: `docker-compose logs celery_worker`
   - Check Redis connection
   - Verify job queue configuration

### Logs and Debugging

View service logs:
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs celery_worker
```

### Reset Everything

To completely reset the application:
```bash
# Stop all services
docker-compose down

# Remove volumes (this will delete all data)
docker-compose down -v

# Rebuild and start
docker-compose up --build
```

## Production Deployment

For production deployment:

1. **Update Environment Variables**
   - Set `DEBUG=false`
   - Use strong `SECRET_KEY`
   - Configure production database
   - Set up SSL certificates

2. **Security Considerations**
   - Change default passwords
   - Configure firewall rules
   - Set up monitoring and logging
   - Enable rate limiting

3. **Scaling**
   - Use multiple Celery workers
   - Set up load balancing
   - Configure database clustering
   - Use CDN for static files

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs for error messages
3. Check the API documentation at http://localhost:8000/docs
4. Create an issue in the repository

## Next Steps

- Explore the API documentation
- Try uploading different document types
- Check out the processing pipeline
- Review the codebase structure
- Contribute to the project
