# GoatMorpho Oracle Cloud Deployment Guide

Complete deployment guide for GoatMorpho on Oracle Cloud Infrastructure with distributed architecture.

## Architecture Overview

```
Internet (goatmorpho.info)
    ↓
Django Instance (Public: 130.61.39.212, Private: 10.0.0.163)
    ↓ (Internal Network)
CV Processing Instance (Private: 10.0.1.25)
```

## Instance Configuration

### Django Instance (VM.Standard.A1.Flex)
- **Public IP**: 130.61.39.212
- **Private IP**: 10.0.0.163
- **Resources**: 1 OCPU, 6GB RAM
- **Role**: Web server, database, user interface
- **Components**: Django, Nginx, PostgreSQL, Redis

### CV Processing Instance (VM.Standard.A1.Flex)
- **Private IP**: 10.0.1.25
- **Resources**: 4 OCPU, 24GB RAM
- **Role**: Computer vision processing
- **Components**: OpenCV, MediaPipe, TensorFlow, FastAPI

## Deployment Steps

### Prerequisites

1. **Domain Configuration**
   - Point `goatmorpho.info` and `www.goatmorpho.info` to `130.61.39.212`
   - Ensure DNS propagation is complete

2. **Instance Access**
   - SSH access to both instances
   - Sudo privileges on both instances

### Step 1: Django Instance Setup

```bash
# SSH to Django instance
ssh ubuntu@130.61.39.212

# Clone deployment files
git clone <your-repo-url> /tmp/goatmorpho-deploy
cd /tmp/goatmorpho-deploy/deploy

# Run Django instance setup
chmod +x deploy.sh
sudo ./deploy.sh
```

This will:
- Install Python, Nginx, PostgreSQL, Redis
- Create application user and directories
- Configure Gunicorn and systemd services
- Setup firewall rules
- Configure Nginx with SSL placeholder

### Step 2: CV Processing Instance Setup

```bash
# SSH to CV instance
ssh ubuntu@10.0.1.25

# Copy deployment files
scp -r ubuntu@130.61.39.212:/tmp/goatmorpho-deploy/deploy/* ./

# Run CV instance setup
chmod +x deploy.sh
sudo ./deploy.sh
```

This will:
- Install OpenCV, MediaPipe, and ARM64-optimized libraries
- Create FastAPI microservice for CV processing
- Configure internal-only firewall access
- Setup systemd service for CV processor

### Step 3: Application Deployment

On Django instance:

```bash
# Copy your application code
sudo cp -r /path/to/your/goatmorpho/* /opt/goatmorpho/app/

# Install dependencies
sudo -u goatmorpho bash -c "
    source /opt/goatmorpho/venv/bin/activate
    cd /opt/goatmorpho/app
    pip install -r requirements_django.txt
"

# Run database migrations
sudo -u goatmorpho /opt/goatmorpho/manage.sh migrate

# Create superuser
sudo -u goatmorpho /opt/goatmorpho/manage.sh createsuperuser

# Collect static files
sudo -u goatmorpho /opt/goatmorpho/manage.sh collectstatic --noinput

# Start services
sudo systemctl start goatmorpho
sudo systemctl enable goatmorpho
```

### Step 4: SSL Certificate Setup

```bash
# On Django instance
sudo certbot --nginx -d goatmorpho.info -d www.goatmorpho.info
```

### Step 5: CV Service Startup

```bash
# On CV instance
sudo systemctl start cvprocessor
sudo systemctl enable cvprocessor

# Test CV service
sudo -u cvprocessor /opt/cvprocessor/venv/bin/python /opt/cvprocessor/test_service.py
```

## Configuration Files

### Environment Variables (Django Instance)

Edit `/opt/goatmorpho/.env`:

```bash
# Django Settings
DJANGO_SECRET_KEY=your-super-secret-key-change-this-in-production
DJANGO_SETTINGS_MODULE=goat_morpho.production_settings
DEBUG=False

# Database Configuration
DB_NAME=goat_morpho
DB_USER=goat_morpho_user
DB_PASSWORD=secure_password_change_this
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_HOST=127.0.0.1

# CV Processing Service
CV_PROCESSING_URL=http://10.0.1.25:8001
```

### Production Settings

The deployment includes optimized production settings:
- Security headers and HTTPS enforcement
- Static file serving with WhiteNoise
- Redis session storage
- PostgreSQL database configuration
- Distributed CV processing integration

## Monitoring and Maintenance

### Service Status

```bash
# Django instance
sudo systemctl status goatmorpho
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis

# CV instance
sudo systemctl status cvprocessor
```

### Logs

```bash
# Django instance
sudo journalctl -u goatmorpho -f
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/goat_morpho/app.log

# CV instance
sudo journalctl -u cvprocessor -f
sudo tail -f /var/log/cvprocessor/service.log
```

### Health Checks

```bash
# Django instance
curl https://goatmorpho.info/health/

# CV instance (from Django instance)
curl http://10.0.1.25:8001/health
```

## Security Considerations

### Firewall Configuration

**Django Instance:**
- SSH (22)
- HTTP/HTTPS (80/443)
- Internal communication with CV instance

**CV Instance:**
- SSH (22)
- CV service (8001) - only from Django instance subnet

### SSL/TLS

- Let's Encrypt certificates for domain
- Automatic renewal configured
- HSTS headers enabled
- Secure cookie settings

### Network Security

- CV instance has no public IP
- Internal communication only
- Firewall rules restrict access

## Troubleshooting

### Common Issues

1. **CV Service Connection Failed**
   ```bash
   # Check CV service status
   ssh ubuntu@10.0.1.25 'sudo systemctl status cvprocessor'
   
   # Test internal connectivity from Django instance
   curl http://10.0.1.25:8001/health
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connection
   sudo -u postgres psql -d goat_morpho -U goat_morpho_user -h localhost
   ```

3. **SSL Certificate Issues**
   ```bash
   # Renew certificate
   sudo certbot renew
   
   # Test certificate
   sudo certbot certificates
   ```

4. **Static Files Not Loading**
   ```bash
   # Recollect static files
   sudo -u goatmorpho /opt/goatmorpho/manage.sh collectstatic --clear --noinput
   
   # Check Nginx configuration
   sudo nginx -t
   ```

### Performance Optimization

1. **Database Optimization**
   ```sql
   -- Connect to PostgreSQL and run
   ANALYZE;
   VACUUM;
   ```

2. **Redis Memory Optimization**
   ```bash
   # Check Redis memory usage
   redis-cli INFO memory
   ```

3. **Monitor Resource Usage**
   ```bash
   # System resources
   htop
   iostat -x 1
   free -h
   df -h
   ```

## Backup and Recovery

### Database Backup

```bash
# Create backup
sudo -u postgres pg_dump goat_morpho > goat_morpho_backup_$(date +%Y%m%d).sql

# Restore backup
sudo -u postgres psql goat_morpho < goat_morpho_backup_YYYYMMDD.sql
```

### Media Files Backup

```bash
# Backup media files
tar -czf media_backup_$(date +%Y%m%d).tar.gz /opt/goatmorpho/app/media/
```

## Cost Optimization

### Current Monthly Estimate
- Django Instance (1 OCPU, 6GB): ~$50-70
- CV Instance (4 OCPU, 24GB): ~$200-280
- Storage & Network: ~$20-50
- **Total**: ~$270-400/month

### Optimization Strategies
1. Use Oracle Cloud Always Free tier where possible
2. Implement auto-scaling for CV instance
3. Use object storage for media files
4. Monitor and optimize resource usage

## Scaling Considerations

### Horizontal Scaling
- Add more CV processing instances behind load balancer
- Implement Redis Cluster for session storage
- Use separate database instance

### Vertical Scaling
- Increase CV instance resources during peak usage
- Add GPU instance for intensive ML workloads

---

**Support**: For issues with deployment, check logs and ensure all services are running. The architecture is designed for cost-effectiveness while maintaining good performance for morphometric analysis workloads.
