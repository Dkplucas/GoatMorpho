# GoatMorpho Single Instance Deployment Guide

## Oracle Cloud Infrastructure Setup
**Optimized for VM.Standard.A1.Flex (4 OCPUs, 24GB RAM)**

### Instance Configuration
- **Shape**: VM.Standard.A1.Flex
- **OCPUs**: 4
- **Memory**: 24GB
- **Public IP**: 130.61.39.212
- **Private IP**: 10.0.0.163
- **Domain**: goatmorpho.info

### Architecture Overview
This deployment runs all services on a single powerful Oracle Cloud instance:
- **Django Application** (Port 80/443 via Nginx)
- **PostgreSQL Database** (Port 5432)
- **Redis Cache** (Port 6379)
- **CV Processing Service** (Port 8001)
- **Nginx Web Server** (Reverse proxy + SSL termination)

## Prerequisites

### Oracle Cloud Setup
1. **Create VM.Standard.A1.Flex instance** with 4 OCPUs and 24GB RAM
2. **Configure networking**:
   - Ensure ports 22, 80, 443 are open in Security Lists
   - Assign public IP: 130.61.39.212
3. **DNS Configuration**:
   - Point `goatmorpho.info` A record to `130.61.39.212`
   - Point `www.goatmorpho.info` A record to `130.61.39.212`

### System Requirements
- Ubuntu 20.04 LTS or later (ARM64)
- Root access via SSH
- Internet connectivity
- Domain name configured

## Quick Start Deployment

### 1. Prepare Source Code
```bash
# On your local machine, prepare the deployment files
scp -r deploy/ ubuntu@130.61.39.212:/tmp/goat_morpho_deploy/
scp -r . ubuntu@130.61.39.212:/tmp/goat_morpho_source/
```

### 2. Run Deployment Script
```bash
# SSH to your Oracle Cloud instance
ssh ubuntu@130.61.39.212

# Switch to root and run deployment
sudo su -
cd /tmp/goat_morpho_deploy
chmod +x single_instance_deploy.sh
./single_instance_deploy.sh
```

### 3. Verify Deployment
```bash
# Run verification script
chmod +x single_instance_verify.sh
./single_instance_verify.sh
```

## Detailed Configuration

### Performance Optimizations

#### PostgreSQL Configuration (24GB RAM)
- **shared_buffers**: 6GB (25% of RAM)
- **effective_cache_size**: 18GB (75% of RAM)  
- **maintenance_work_mem**: 1GB
- **work_mem**: 64MB
- **max_connections**: 200

#### Redis Configuration
- **maxmemory**: 2GB
- **maxmemory-policy**: allkeys-lru
- **Persistence disabled** for better performance

#### Gunicorn Configuration
- **Workers**: 8 (2 per CPU core)
- **Worker class**: gevent (async)
- **Worker connections**: 1000
- **Max requests**: 1000

#### System Optimizations
- **vm.swappiness**: 10
- **vm.dirty_ratio**: 15
- **net.core.somaxconn**: 1024
- **fs.file-max**: 100000

### Security Configuration

#### Firewall (UFW)
```bash
# Enabled ports
22/tcp    - SSH
80/tcp    - HTTP
443/tcp   - HTTPS
```

#### SSL Certificate
- **Let's Encrypt** certificate for goatmorpho.info
- **Auto-renewal** via certbot
- **HSTS** enabled with 1-year max-age

#### Fail2ban
- **SSH protection** enabled
- **Rate limiting** for login attempts

### File Structure
```
/opt/goat_morpho/                 # Application directory
├── goat_morpho/                  # Django project
├── measurements/                 # Main application
├── media/                        # User uploads
├── staticfiles/                  # Static files
├── venv/                         # Python virtual environment
├── .env                          # Environment variables
└── manage.py                     # Django management

/var/log/goat_morpho/             # Application logs
├── app.log                       # Main application log
└── error.log                     # Error log

/etc/nginx/sites-available/       # Nginx configuration
└── goat-morpho                   # Site configuration

/etc/systemd/system/              # Service files
├── goat-morpho.service           # Django application service
├── goat-morpho.socket            # Gunicorn socket
└── goat-morpho-cv.service        # CV processing service
```

## Service Management

### Start/Stop Services
```bash
# Start all services
systemctl start postgresql redis-server
systemctl start goat-morpho.socket goat-morpho.service
systemctl start goat-morpho-cv.service nginx

# Stop all services
systemctl stop nginx goat-morpho-cv.service
systemctl stop goat-morpho.service goat-morpho.socket
systemctl stop redis-server postgresql

# Restart application only
systemctl restart goat-morpho.service goat-morpho-cv.service
```

### View Logs
```bash
# Application logs
tail -f /var/log/goat_morpho/app.log

# Service logs
journalctl -u goat-morpho.service -f
journalctl -u goat-morpho-cv.service -f
journalctl -u nginx.service -f

# System logs
journalctl -xe
```

## Monitoring and Maintenance

### System Monitoring
```bash
# Run monitoring script
/opt/goat_morpho/monitor.sh

# Check resource usage
htop
iostat -x 1
free -h
df -h
```

### Database Maintenance
```bash
# Connect to database
sudo -u postgres psql -d goat_morpho

# Check database size
SELECT pg_size_pretty(pg_database_size('goat_morpho'));

# Check active connections
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

# Vacuum and analyze
VACUUM ANALYZE;
```

### Cache Management
```bash
# Check Redis memory usage
redis-cli info memory

# Clear cache
redis-cli flushdb

# Monitor Redis
redis-cli monitor
```

## Backup and Recovery

### Database Backup
```bash
# Create backup
sudo -u postgres pg_dump goat_morpho > /backup/goat_morpho_$(date +%Y%m%d).sql

# Restore backup
sudo -u postgres psql -d goat_morpho < /backup/goat_morpho_20240726.sql
```

### Application Backup
```bash
# Backup media files
tar -czf /backup/media_$(date +%Y%m%d).tar.gz /opt/goat_morpho/media/

# Backup configuration
tar -czf /backup/config_$(date +%Y%m%d).tar.gz /opt/goat_morpho/.env /etc/nginx/sites-available/goat-morpho
```

## Scaling and Optimization

### Vertical Scaling
To increase instance resources:
1. Stop application: `systemctl stop goat-morpho.service goat-morpho-cv.service`
2. Resize instance in Oracle Cloud Console
3. Update configurations:
   - PostgreSQL: Adjust `shared_buffers` and `effective_cache_size`
   - Gunicorn: Increase workers (2 per CPU)
   - Redis: Increase `maxmemory`
4. Restart services

### Performance Tuning
```bash
# Monitor database performance
sudo -u postgres psql -d goat_morpho -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Monitor application performance
tail -f /var/log/goat_morpho/app.log | grep "ERROR\|WARNING"

# Check slow requests
grep "slow" /var/log/nginx/access.log
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
systemctl status goat-morpho.service

# Check logs
journalctl -u goat-morpho.service -n 50

# Check configuration
nginx -t
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
systemctl status postgresql

# Check connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Reset connections
systemctl restart postgresql
```

#### High Memory Usage
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -20

# Clear cache if needed
echo 3 > /proc/sys/vm/drop_caches
```

#### SSL Certificate Issues
```bash
# Check certificate status
certbot certificates

# Renew certificate
certbot renew --dry-run

# Force renewal
certbot renew --force-renewal
```

### Performance Issues
1. **High CPU**: Check CV processing queue, reduce concurrent workers
2. **High Memory**: Tune PostgreSQL buffers, restart services
3. **Slow Response**: Check database queries, optimize indexes
4. **Storage Full**: Clean old logs, optimize media files

## Maintenance Schedule

### Daily
- Monitor system resources (`/opt/goat_morpho/monitor.sh`)
- Check application logs for errors
- Verify SSL certificate status

### Weekly
- Review performance metrics
- Clean old log files
- Update system packages: `apt update && apt upgrade`

### Monthly
- Backup database and media files
- Analyze database performance
- Review security logs (fail2ban)
- Check disk usage and cleanup

## Support and Resources

### Log Locations
- **Application**: `/var/log/goat_morpho/app.log`
- **Nginx Access**: `/var/log/nginx/access.log`
- **Nginx Error**: `/var/log/nginx/error.log`
- **System**: `journalctl -xe`

### Configuration Files
- **Django**: `/opt/goat_morpho/goat_morpho/single_instance_settings.py`
- **Environment**: `/opt/goat_morpho/.env`
- **Nginx**: `/etc/nginx/sites-available/goat-morpho`
- **PostgreSQL**: `/etc/postgresql/*/main/postgresql.conf`
- **Redis**: `/etc/redis/redis.conf`

### Default Credentials
- **Django Admin**: 
  - Username: `admin`
  - Password: `GoatMorpho2024!Admin`
  - URL: `https://goatmorpho.info/admin/`

### URLs
- **Application**: `https://goatmorpho.info`
- **Admin Interface**: `https://goatmorpho.info/admin/`
- **API Documentation**: `https://goatmorpho.info/api/`

## Cost Optimization

### Current Configuration Cost
- **VM.Standard.A1.Flex (4 OCPUs, 24GB)**: ~$0.06/hour × 24h × 30 days = **~$43.20/month**
- **Block Storage (200GB)**: ~$0.0255/GB × 200GB = **~$5.10/month**
- **Network (Outbound)**: ~$0.0085/GB for first 10TB
- **Total Estimated**: **~$48-55/month**

### Cost Optimization Tips
1. **Use Oracle Always Free Tier** when possible
2. **Optimize storage**: Remove unused files, compress media
3. **Monitor bandwidth**: Optimize image sizes
4. **Schedule downtime**: Stop instance during low usage periods
5. **Use Oracle Cloud Credits**: Apply available credits

---

**Note**: Remember to change default passwords and configure email settings in `/opt/goat_morpho/.env` after deployment.
