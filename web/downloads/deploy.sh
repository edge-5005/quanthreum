#!/usr/bin/env bash
# =====================================================================
# Quanthreum (QTH) - Automated 1-Click Server Deploy Script
# For Ubuntu 22.04 / 24.04 LTS or Debian 11/12
# =====================================================================

set -e

echo "============================================================"
echo "  Deploying Quanthreum (QTH) Node & Web Portal"
echo "============================================================"

# 1. Update system & install prerequisites
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip nginx certbot python3-certbot-nginx git curl ufw

# 2. Setup directories
sudo mkdir -p /var/www/quanthreum
sudo mkdir -p /var/lib/quanthreum

# 3. Copy files to /var/www/quanthreum
sudo cp -r . /var/www/quanthreum/
sudo chown -R www-data:www-data /var/www/quanthreum
sudo chown -R www-data:www-data /var/lib/quanthreum

# 4. Install systemd service
sudo cp quanthreum.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable quanthreum
sudo systemctl restart quanthreum

# 5. Configure Nginx
sudo cp nginx.conf /etc/nginx/sites-available/quanthreum
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/quanthreum /etc/nginx/sites-enabled/quanthreum
sudo nginx -t
sudo systemctl restart nginx

# 6. Configure Firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

echo ""
echo "============================================================"
echo "  Quanthreum is now LIVE!"
echo "  Local Node URL: http://127.0.0.1:8545"
echo "  Web Proxy URL:  http://$(curl -s ifconfig.me)"
echo ""
echo "  To enable free SSL certificate (HTTPS):"
echo "  sudo certbot --nginx -d your-domain.com"
echo "============================================================"
