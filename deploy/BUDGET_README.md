# 💰 GoatMorpho Budget Deployment Guide

**Ultra-low cost deployment for Oracle Cloud Infrastructure**  
Perfect for beginners, learning projects, and tight budgets!

---

## 🎯 **Budget Architecture Overview**

```
Internet (goatmorpho.info)
    ↓
Single VM Instance (130.61.39.212)
├── Django Web App
├── Integrated CV Processing
├── SQLite Database
├── File-based Cache
└── Nginx Web Server
```

**Everything runs on ONE instance!**

---

## 💵 **Cost Breakdown**

| Resource | Configuration | Monthly Cost |
|----------|---------------|--------------|
| **Compute** | VM.Standard.A1.Flex (2 OCPU, 12GB) | **$0** (Always Free) |
| **Storage** | 100GB Block Volume | **$2** |
| **Network** | 10TB outbound transfer | **$0** (Always Free) |
| **Domain** | goatmorpho.info | **$12-15** |
| **SSL** | Let's Encrypt | **$0** |
| **Total** | | **$14-17/month** |

**🎉 That's 95% cheaper than the original estimate!**

---

## ⚡ **Quick Deployment**

### **Step 1: Prepare Your Instance**
```bash
# SSH to your Oracle Cloud instance
ssh ubuntu@130.61.39.212

# Download deployment script
wget https://your-repo/budget_deploy.sh
chmod +x budget_deploy.sh

# Run budget deployment
sudo ./budget_deploy.sh
```

### **Step 2: Deploy Your Code**
```bash
# Copy your GoatMorpho code
sudo cp -r /path/to/goatmorpho/* /opt/goatmorpho/app/

# Install integrated CV processor
sudo cp /opt/goatmorpho/integrated_cv_processor.py /opt/goatmorpho/app/measurements/cv_processor.py
sudo cp budget_settings.py /opt/goatmorpho/app/goat_morpho/budget_settings.py

# Setup database
sudo -u goatmorpho /opt/goatmorpho/manage.sh migrate
sudo -u goatmorpho /opt/goatmorpho/manage.sh createsuperuser
sudo -u goatmorpho /opt/goatmorpho/manage.sh collectstatic --noinput

# Start services
sudo systemctl start goatmorpho
sudo systemctl enable goatmorpho
```

### **Step 3: Configure SSL**
```bash
# Setup free SSL certificate
sudo certbot --nginx -d goatmorpho.info -d www.goatmorpho.info
```

---

## 🔧 **Budget Optimizations**

### **Database: SQLite instead of PostgreSQL**
- ✅ No separate database instance cost
- ✅ Zero configuration required
- ✅ Perfect for small to medium workloads
- ⚠️ Single user writes (perfect for web apps)

### **Cache: File-based instead of Redis**
- ✅ No Redis instance cost
- ✅ Uses local disk for caching
- ✅ Automatic cleanup
- ⚠️ Not shared across instances (perfect for single instance)

### **CV Processing: Integrated instead of Distributed**
- ✅ No separate CV instance cost
- ✅ Lightweight MediaPipe model
- ✅ Optimized for ARM64
- ⚠️ Sequential processing (suitable for low traffic)

### **Resource Allocation**
```
2 OCPU ARM64 Processor:
├── Django/Gunicorn: 1 OCPU
├── CV Processing: 0.5 OCPU
├── Nginx: 0.3 OCPU
└── System: 0.2 OCPU

12GB RAM:
├── Django App: 4GB
├── CV Processing: 4GB
├── SQLite: 1GB
├── File Cache: 1GB
└── System: 2GB
```

---

## 📊 **Performance Expectations**

| Metric | Budget Deployment | Original Plan |
|--------|-------------------|---------------|
| **Concurrent Users** | 5-10 | 10-20 |
| **Image Processing** | 60-120 seconds | 30-60 seconds |
| **Monthly Cost** | $15-17 | $270-400 |
| **Uptime** | 99%+ | 99%+ |
| **Storage** | 100GB | 200-500GB |

**Perfect for:**
- Learning and development
- Small user base (< 50 users)
- Proof of concept
- Personal projects
- Academic research

---

## 🛠️ **Deployment Configuration**

### **Environment Variables** (`/opt/goatmorpho/.env`)
```bash
# Minimal configuration for budget deployment
DJANGO_SECRET_KEY=your-super-secret-key-change-this
DJANGO_SETTINGS_MODULE=goat_morpho.budget_settings
DEBUG=False
```

### **Budget Settings Features**
- SQLite database configuration
- File-based caching
- Reduced security headers for simplicity
- Smaller file upload limits (5MB vs 10MB)
- Simplified logging
- Conservative pagination (10 items vs 20)

### **Nginx Configuration**
- Basic SSL settings
- Reduced timeouts for budget
- Smaller client max body size
- Simple caching headers

### **Gunicorn Configuration**
- 2 workers (perfect for 2 OCPU)
- Reduced timeouts
- Minimal logging
- Conservative resource usage

---

## 📈 **Scaling Path**

### **When to Upgrade:**
1. **More than 10 concurrent users**
2. **Processing > 100 images/day**
3. **Need faster processing times**
4. **Require high availability**

### **Upgrade Options:**
```
Budget → Standard → Enterprise
$15/mo → $100/mo → $400/mo

Single    Dual      Distributed
Instance  Instance  Architecture
```

---

## 🔍 **Monitoring & Maintenance**

### **Health Checks**
```bash
# Check services
sudo systemctl status goatmorpho nginx

# Check resources
htop
df -h
free -h

# Check logs
sudo journalctl -u goatmorpho -f
tail -f /opt/goatmorpho/logs/gunicorn_error.log
```

### **Backup Strategy**
```bash
# Database backup (SQLite)
cp /opt/goatmorpho/app/db.sqlite3 ~/backup_$(date +%Y%m%d).sqlite3

# Media files backup
tar -czf ~/media_backup_$(date +%Y%m%d).tar.gz /opt/goatmorpho/app/media/
```

### **Automated Maintenance**
```bash
# Add to crontab (sudo crontab -e)
0 2 * * 0 systemctl restart goatmorpho  # Weekly restart
0 3 * * 0 find /tmp/django_cache -mtime +7 -delete  # Cache cleanup
```

---

## ⚠️ **Budget Limitations**

### **What's Different:**
- **Single instance** (no high availability)
- **Sequential processing** (one image at a time)
- **SQLite database** (not suitable for high concurrency)
- **Local file cache** (lost on restart)
- **Smaller upload limits** (5MB vs 10MB)
- **Basic monitoring** (no advanced metrics)

### **What's the Same:**
- **Full GoatMorpho functionality**
- **SSL encryption**
- **Professional domain**
- **Computer vision processing**
- **User authentication**
- **Data export features**

---

## 🚀 **Getting Started Checklist**

- [ ] Setup Oracle Cloud Always Free account
- [ ] Create VM.Standard.A1.Flex instance (2 OCPU, 12GB)
- [ ] Configure domain DNS to point to public IP
- [ ] Run budget deployment script
- [ ] Deploy application code
- [ ] Configure SSL certificate
- [ ] Test image upload and processing
- [ ] Create admin user
- [ ] Monitor resource usage

---

## 💡 **Pro Tips for Budget Success**

1. **Use Oracle Cloud Always Free Tier** - Maximize free resources
2. **Optimize images before upload** - Smaller files = faster processing
3. **Monitor resource usage** - Stay within limits
4. **Regular maintenance** - Keep system updated
5. **Backup regularly** - SQLite databases are files
6. **Scale when needed** - Easy upgrade path available

---

**🎉 Perfect for getting started with GoatMorpho without breaking the bank!**

This budget deployment gives you a fully functional goat morphometric analysis platform for less than the cost of a Netflix subscription! 🐐💰
