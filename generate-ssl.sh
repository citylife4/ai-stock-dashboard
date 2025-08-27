#!/bin/bash

# Script to generate self-signed SSL certificates for development
# For production, replace these with real certificates from Let's Encrypt or a CA

SSL_DIR="./ssl"
DOMAIN="localhost"

echo "🔐 Generating SSL certificates for AI Stock Dashboard..."

# Create SSL directory
mkdir -p "$SSL_DIR"

# Generate private key
openssl genrsa -out "$SSL_DIR/privkey.pem" 2048

# Generate certificate signing request
openssl req -new -key "$SSL_DIR/privkey.pem" -out "$SSL_DIR/cert.csr" -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"

# Generate self-signed certificate
openssl x509 -req -in "$SSL_DIR/cert.csr" -signkey "$SSL_DIR/privkey.pem" -out "$SSL_DIR/fullchain.pem" -days 365

# Clean up CSR file
rm "$SSL_DIR/cert.csr"

# Set proper permissions
chmod 600 "$SSL_DIR/privkey.pem"
chmod 644 "$SSL_DIR/fullchain.pem"

echo "✅ SSL certificates generated successfully!"
echo "📁 Location: $SSL_DIR/"
echo "🔑 Private Key: $SSL_DIR/privkey.pem"
echo "📜 Certificate: $SSL_DIR/fullchain.pem"
echo ""
echo "⚠️  NOTE: These are self-signed certificates for development only."
echo "   For production, use certificates from Let's Encrypt or a trusted CA."
echo ""
echo "🚀 You can now start the application with HTTPS support!"
echo "   docker-compose -f docker-compose.prod.yml up -d"
