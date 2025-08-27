#!/bin/bash

# Script to set up Let's Encrypt SSL certificates for production
# Requires: certbot, your domain name, and DNS pointing to this server

DOMAIN="your-domain.com"  # Replace with your actual domain
EMAIL="admin@your-domain.com"  # Replace with your email

echo "🔐 Setting up Let's Encrypt SSL certificates..."
echo "📧 Email: $EMAIL"
echo "🌐 Domain: $DOMAIN"
echo ""

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    sudo apt update
    sudo apt install -y certbot
fi

# Create SSL directory
mkdir -p ./ssl

echo "🚀 Obtaining SSL certificates from Let's Encrypt..."
echo "⚠️  Make sure your domain DNS is pointing to this server!"
echo ""

# Stop any running containers that might use port 80
docker-compose -f docker-compose.prod.yml down

# Obtain certificates using standalone mode
sudo certbot certonly \
    --standalone \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN"

# Copy certificates to local SSL directory
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ./ssl/
    sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" ./ssl/
    sudo chown $USER:$USER ./ssl/*.pem
    chmod 644 ./ssl/fullchain.pem
    chmod 600 ./ssl/privkey.pem
    
    echo "✅ SSL certificates obtained successfully!"
    echo "📁 Certificates copied to ./ssl/"
    echo ""
    echo "🚀 Starting application with HTTPS..."
    docker-compose -f docker-compose.prod.yml up -d
    
    echo ""
    echo "🌐 Your application is now available at:"
    echo "   HTTP:  http://$DOMAIN:34197"
    echo "   HTTPS: https://$DOMAIN:34198"
    
else
    echo "❌ Failed to obtain SSL certificates"
    echo "Please check:"
    echo "1. Domain DNS is pointing to this server"
    echo "2. Port 80 is accessible from the internet"
    echo "3. Domain name is correct"
fi

echo ""
echo "📋 To renew certificates automatically, add this to crontab:"
echo "0 12 * * * /usr/bin/certbot renew --quiet --post-hook 'docker-compose -f /path/to/docker-compose.prod.yml restart frontend'"
