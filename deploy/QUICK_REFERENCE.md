# 🚀 GoatMorpho Quick Deployment Reference

## 📝 **Your Instance Details**
```
Instance: VM.Standard.A1.Flex (4 OCPUs, 24GB RAM)
Public IP: 130.61.39.212
Private IP: 10.0.0.163
Domain: goatmorpho.info
```

## ⚡ **Quick Commands**

### 1. **Upload Files** (from your Windows machine):
```powershell
cd f:\Database\Deploy\GoatMorpho
scp -r deploy/ ubuntu@130.61.39.212:/tmp/goat_morpho_deploy/
scp -r . ubuntu@130.61.39.212:/tmp/goat_morpho_source/
```

### 2. **Deploy** (on Oracle Cloud instance):
```bash
ssh ubuntu@130.61.39.212
sudo su -
cd /tmp/goat_morpho_deploy
chmod +x single_instance_deploy.sh
./single_instance_deploy.sh
```

### 3. **Verify**:
```bash
chmod +x single_instance_verify.sh
./single_instance_verify.sh
```

### 4. **Test Access**:
- **Local**: `curl http://localhost/`
- **Public**: Open browser → `http://130.61.39.212`
- **Domain**: Open browser → `http://goatmorpho.info`
- **Admin**: `https://goatmorpho.info/admin/` (admin/GoatMorpho2024!Admin)

## 🔧 **Essential Service Commands**

### **Check Status**:
```bash
systemctl status postgresql redis-server goat-morpho.service nginx
```

### **Restart Services**:
```bash
systemctl restart goat-morpho.service goat-morpho-cv.service nginx
```

### **View Logs**:
```bash
tail -f /var/log/goat_morpho/app.log
journalctl -u goat-morpho.service -f
```

### **Monitor System**:
```bash
/opt/goat_morpho/monitor.sh
```

## 🚨 **Emergency Commands**

### **If Services Won't Start**:
```bash
# Check what's wrong
systemctl status goat-morpho.service
journalctl -u goat-morpho.service -n 50

# Fix permissions
chown -R goat_morpho:goat_morpho /opt/goat_morpho

# Restart everything
systemctl restart postgresql redis-server
systemctl restart goat-morpho.service goat-morpho-cv.service
systemctl restart nginx
```

### **If SSL Certificate Fails**:
```bash
# Install manually later
certbot --nginx -d goatmorpho.info -d www.goatmorpho.info
```

### **If Database Issues**:
```bash
# Check PostgreSQL
sudo -u postgres psql -d goat_morpho -c "SELECT 1;"
```

## 📍 **Important File Locations**
- **App Directory**: `/opt/goat_morpho/`
- **Environment**: `/opt/goat_morpho/.env`
- **Logs**: `/var/log/goat_morpho/app.log`
- **Nginx Config**: `/etc/nginx/sites-available/goat-morpho`

## ✅ **Success Indicators**
- All services show "✅ running" in verification
- Website loads at `http://goatmorpho.info`
- Admin panel accessible at `/admin/`
- CV service responds at `http://localhost:8001/health`

## 🔄 **Next Steps After Deployment**
1. Change admin password
2. Test image upload and processing
3. Configure email settings (optional)
4. Set up regular backups
