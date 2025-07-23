# GoatMeasure Pro - Deployment Package

## Quick Start

1. Upload this package to your Ubuntu server
2. Install Node.js 18+ and PostgreSQL
3. Run deployment:

```bash
cd goatmeasure-pro
cp .env.example .env
# Edit .env with your database credentials
./deploy.sh
npm start
```

## Requirements

- Node.js 18+
- PostgreSQL 13+
- 2GB RAM minimum
- 10GB disk space

## Production Setup

```bash
# Install PM2 for process management
npm install -g pm2

# Start with PM2
pm2 start deployment.config.js

# Save PM2 configuration
pm2 save
pm2 startup
```

## Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
