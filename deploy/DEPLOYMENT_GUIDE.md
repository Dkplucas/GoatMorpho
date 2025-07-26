# GoatMorpho Deployment Guide - Step by Step
**Oracle Cloud Single Instance Deployment**

## 🎯 **Your Configuration**
- **Instance**: VM.Standard.A1.Flex (4 OCPUs, 24GB RAM)
- **Public IP**: 130.61.39.212
- **Private IP**: 10.0.0.163
- **Domain**: goatmorpho.info

---

## 📋 **Pre-Deployment Checklist**

### ✅ **Step 1: Verify Oracle Cloud Instance**
1. **Log into Oracle Cloud Console**
2. **Verify your instance is running**:
   - Shape: VM.Standard.A1.Flex
   - OCPUs: 4
   - Memory: 24GB
   - Public IP: 130.61.39.212

3. **Check Security List Rules**:
   ```
   Ingress Rules:
   - Port 22 (SSH): 0.0.0.0/0
   - Port 80 (HTTP): 0.0.0.0/0  
   - Port 443 (HTTPS): 0.0.0.0/0
   ```

### ✅ **Step 2: Configure DNS**
1. **Go to your domain registrar** (where you bought goatmorpho.info)
2. **Add these DNS records**:
   ```
   Type: A
   Name: @
   Value: 130.61.39.212
   TTL: 300
   
   Type: A  
   Name: www
   Value: 130.61.39.212
   TTL: 300
   ```
3. **Wait 5-15 minutes** for DNS propagation
4. **Test DNS**: Open command prompt and run:
   ```cmd
   nslookup goatmorpho.info
   ```
   Should return: 130.61.39.212

---

## 🚀 **Deployment Process**

### ✅ **Step 3: Connect to Your Instance**
1. **Open PowerShell/Command Prompt**
2. **Connect via SSH**:
   ```powershell
   ssh ubuntu@130.61.39.212
   ```
   - If prompted about authenticity, type `yes`
   - Enter your SSH key passphrase if you have one

### ✅ **Step 4: Prepare Your Local Files**
1. **Open another PowerShell window** (keep SSH connection open)
2. **Navigate to your GoatMorpho folder**:
   ```powershell
   cd f:\Database\Deploy\GoatMorpho
   ```

3. **Upload deployment files**:
   ```powershell
   scp -r deploy/ ubuntu@130.61.39.212:/tmp/goat_morpho_deploy/
   ```

4. **Upload source code**:
   ```powershell
   scp -r . ubuntu@130.61.39.212:/tmp/goat_morpho_source/
   ```

### ✅ **Step 5: Run the Deployment Script**
1. **Go back to your SSH window**
2. **Switch to root user**:
   ```bash
   sudo su -
   ```

3. **Navigate to deployment directory**:
   ```bash
   cd /tmp/goat_morpho_deploy
   ```

4. **Make script executable**:
   ```bash
   chmod +x single_instance_deploy.sh
   ```

5. **Start deployment** (this will take 15-20 minutes):
   ```bash
   ./single_instance_deploy.sh
   ```

   **What to expect**:
   - The script will show colored output (blue=info, green=success, red=error)
   - You'll see packages being installed
   - Database and services being configured
   - This is normal and expected!

### ✅ **Step 6: Monitor the Deployment**
Watch for these key stages:
1. ✅ **System update** (2-3 minutes)
2. ✅ **Package installation** (5-7 minutes)
3. ✅ **Database setup** (2-3 minutes)
4. ✅ **Application configuration** (3-5 minutes)
5. ✅ **Service startup** (2-3 minutes)
6. ✅ **SSL certificate** (1-2 minutes)

### ✅ **Step 7: Handle SSL Certificate Setup**
When you see:
```
Installing SSL certificate...
```

**If prompted for email**, enter: `admin@goatmorpho.info`

**If you see an error about DNS**, it means:
- DNS hasn't propagated yet (wait 10 more minutes)
- Or domain isn't pointing to your IP yet

**Don't worry!** You can install SSL later with:
```bash
certbot --nginx -d goatmorpho.info -d www.goatmorpho.info
```

---

## 🔍 **Verification Steps**

### ✅ **Step 8: Verify Deployment**
1. **Run verification script**:
   ```bash
   chmod +x single_instance_verify.sh
   ./single_instance_verify.sh
   ```

2. **Look for these SUCCESS messages**:
   ```
   [SUCCESS] postgresql is running
   [SUCCESS] redis-server is running  
   [SUCCESS] goat-morpho.service is running
   [SUCCESS] goat-morpho-cv.service is running
   [SUCCESS] nginx is running
   [SUCCESS] All systems operational! ✅
   ```

### ✅ **Step 9: Test Your Application**
1. **Test local access first**:
   ```bash
   curl http://localhost/
   ```
   Should return HTML content

2. **Test from your computer**:
   - Open browser: `http://130.61.39.212`
   - Should show GoatMorpho website

3. **Test domain** (if DNS is ready):
   - Open browser: `http://goatmorpho.info`
   - Should show GoatMorpho website

4. **Test HTTPS** (if SSL certificate installed):
   - Open browser: `https://goatmorpho.info`
   - Should show secure GoatMorpho website

### ✅ **Step 10: Access Admin Interface**
1. **Go to admin panel**:
   - URL: `https://goatmorpho.info/admin/` (or use IP if no SSL)
   - Username: `admin`
   - Password: `GoatMorpho2024!Admin`

2. **Change admin password immediately**:
   - Click your username (top right)
   - Click "Change password"
   - Set a secure new password

---

## 🛠️ **Post-Deployment Configuration**

### ✅ **Step 11: Configure Email (Optional)**
1. **Edit environment file**:
   ```bash
   nano /opt/goat_morpho/.env
   ```

2. **Update email settings**:
   ```
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

3. **Restart application**:
   ```bash
   systemctl restart goat-morpho.service
   ```

### ✅ **Step 12: Test CV Processing**
1. **Check CV service**:
   ```bash
   curl http://localhost:8001/health
   ```

2. **Should return**:
   ```json
   {"status": "healthy", "timestamp": "...", "stats": {...}}
   ```

### ✅ **Step 13: Set Up Monitoring**
1. **Create monitoring script**:
   ```bash
   /opt/goat_morpho/monitor.sh
   ```

2. **Set up daily monitoring** (optional):
   ```bash
   echo "0 9 * * * /opt/goat_morpho/monitor.sh >> /var/log/goat_morpho/daily_status.log" | crontab -
   ```

---

## 🚨 **Troubleshooting Guide**

### ❌ **If Deployment Fails**

#### **Database Issues**:
```bash
# Check PostgreSQL
systemctl status postgresql
sudo -u postgres psql -c "SELECT version();"
```

#### **Service Issues**:
```bash
# Check service status
systemctl status goat-morpho.service
journalctl -u goat-morpho.service -n 50
```

#### **Nginx Issues**:
```bash
# Test nginx configuration
nginx -t
systemctl status nginx
```

#### **Permission Issues**:
```bash
# Fix permissions
chown -R goat_morpho:goat_morpho /opt/goat_morpho
chmod -R 755 /opt/goat_morpho
```

### ❌ **If Website Not Accessible**

1. **Check if services are running**:
   ```bash
   systemctl status nginx goat-morpho.service
   ```

2. **Check firewall**:
   ```bash
   ufw status
   ```

3. **Check Oracle Cloud Security Lists** in the console

4. **Test local access**:
   ```bash
   curl -I http://localhost/
   ```

### ❌ **If SSL Certificate Fails**

1. **Check DNS first**:
   ```bash
   nslookup goatmorpho.info
   ```

2. **Try manual certificate installation**:
   ```bash
   certbot --nginx -d goatmorpho.info -d www.goatmorpho.info --email admin@goatmorpho.info --agree-tos --non-interactive
   ```

3. **If still fails, use HTTP for now** and retry SSL later

---

## ✅ **Success Checklist**

When deployment is complete, you should have:

- [ ] GoatMorpho website accessible at `http://goatmorpho.info`
- [ ] HTTPS working at `https://goatmorpho.info` (if SSL installed)
- [ ] Admin panel accessible at `/admin/`
- [ ] CV processing service running on port 8001
- [ ] All services showing as "running" in verification script
- [ ] Database accessible and migrations applied
- [ ] Redis cache working
- [ ] Log files being created in `/var/log/goat_morpho/`

---

## 🎉 **What's Next?**

1. **Upload sample goat images** to test the morphometric analysis
2. **Create user accounts** for your team
3. **Configure backup procedures** for your data
4. **Set up monitoring alerts** (optional)
5. **Plan for scaling** if you need more resources later

---

## 📞 **Need Help?**

If you encounter issues:

1. **Run the verification script**: `./single_instance_verify.sh`
2. **Check logs**: `tail -f /var/log/goat_morpho/app.log`
3. **Check service status**: `systemctl status goat-morpho.service`
4. **Review this guide** for troubleshooting steps

Your GoatMorpho application should now be fully deployed and ready to use! 🐐📏
