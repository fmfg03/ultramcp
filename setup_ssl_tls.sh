#!/bin/bash

# MCP Enterprise SSL/TLS Setup Script
# Configura certificados SSL automáticos con Let's Encrypt

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración
DOMAIN=${DOMAIN:-"mcp-enterprise.com"}
EMAIL=${SSL_EMAIL:-"admin@mcp-enterprise.com"}
NGINX_CONF_DIR="/etc/nginx"
SSL_DIR="/etc/letsencrypt"
CERTBOT_DIR="/var/www/certbot"

echo -e "${GREEN}🔒 MCP Enterprise SSL/TLS Setup${NC}"
echo "=================================="
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Verificar que estamos ejecutando como root
if [[ $EUID -ne 0 ]]; then
   error "Este script debe ejecutarse como root"
fi

# Instalar dependencias
log "Instalando dependencias..."
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx openssl

# Crear directorios necesarios
log "Creando directorios SSL..."
mkdir -p $SSL_DIR
mkdir -p $CERTBOT_DIR
mkdir -p $NGINX_CONF_DIR/sites-available
mkdir -p $NGINX_CONF_DIR/sites-enabled
mkdir -p /var/log/nginx

# Generar certificado auto-firmado temporal
log "Generando certificado temporal..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout $SSL_DIR/temp-$DOMAIN.key \
    -out $SSL_DIR/temp-$DOMAIN.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"

# Configuración inicial de Nginx
log "Configurando Nginx inicial..."
cat > $NGINX_CONF_DIR/sites-available/mcp-enterprise << EOF
# Configuración inicial para obtener certificado SSL
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Permitir verificación de Let's Encrypt
    location /.well-known/acme-challenge/ {
        root $CERTBOT_DIR;
    }
    
    # Redirigir todo lo demás a HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# Configuración HTTPS temporal
server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # Certificado temporal
    ssl_certificate $SSL_DIR/temp-$DOMAIN.crt;
    ssl_certificate_key $SSL_DIR/temp-$DOMAIN.key;
    
    # Configuración SSL básica
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Proxy a backend MCP
    location /api/ {
        proxy_pass http://localhost:3000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
    }
    
    # Proxy a Grafana
    location /grafana/ {
        proxy_pass http://localhost:3001/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Servir frontend
    location / {
        proxy_pass http://localhost:5174/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Habilitar sitio
ln -sf $NGINX_CONF_DIR/sites-available/mcp-enterprise $NGINX_CONF_DIR/sites-enabled/

# Configuración principal de Nginx
log "Configurando Nginx principal..."
cat > $NGINX_CONF_DIR/nginx.conf << EOF
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    # Basic Settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;
    
    # MIME
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_ecdh_curve secp384r1;
    ssl_session_timeout 10m;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' wss: https:;";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()";
    
    # Logging
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;
    
    # Gzip Settings
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Rate Limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=login:10m rate=1r/s;
    
    # Include sites
    include /etc/nginx/sites-enabled/*;
}
EOF

# Verificar configuración de Nginx
log "Verificando configuración de Nginx..."
nginx -t || error "Error en configuración de Nginx"

# Reiniciar Nginx
log "Reiniciando Nginx..."
systemctl restart nginx
systemctl enable nginx

# Obtener certificado SSL real
log "Obteniendo certificado SSL de Let's Encrypt..."
if certbot --nginx -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --no-eff-email --redirect; then
    log "✅ Certificado SSL obtenido exitosamente"
else
    warning "No se pudo obtener certificado SSL automáticamente. Usando certificado temporal."
fi

# Configurar renovación automática
log "Configurando renovación automática..."
cat > /etc/cron.d/certbot << EOF
# Renovar certificados SSL automáticamente
0 12 * * * root test -x /usr/bin/certbot -a \! -d /run/systemd/system && perl -e 'sleep int(rand(43200))' && certbot -q renew --nginx
EOF

# Configuración SSL avanzada
log "Aplicando configuración SSL avanzada..."
cat > $NGINX_CONF_DIR/sites-available/mcp-enterprise << EOF
# Redirigir HTTP a HTTPS
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Permitir verificación de Let's Encrypt
    location /.well-known/acme-challenge/ {
        root $CERTBOT_DIR;
    }
    
    # Redirigir todo lo demás a HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# Configuración HTTPS principal
server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # Certificados SSL
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # Configuración SSL avanzada
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_ecdh_curve secp384r1;
    ssl_session_timeout 10m;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/$DOMAIN/chain.pem;
    
    # OCSP Stapling
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Rate limiting para API
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://localhost:3000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Rate limiting para login
    location /api/auth/login {
        limit_req zone=login burst=5 nodelay;
        
        proxy_pass http://localhost:3000/auth/login;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # WebSocket para notificaciones
    location /ws/ {
        proxy_pass http://localhost:8765/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }
    
    # Webhooks
    location /webhooks/ {
        proxy_pass http://localhost:8080/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Grafana
    location /grafana/ {
        proxy_pass http://localhost:3001/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Headers específicos para Grafana
        proxy_set_header X-Forwarded-Server \$host;
        proxy_set_header X-Forwarded-Host \$host;
    }
    
    # Prometheus (solo acceso interno)
    location /prometheus/ {
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
        
        proxy_pass http://localhost:9091/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Frontend estático
    location / {
        proxy_pass http://localhost:5174/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Cache para assets estáticos
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header X-Content-Type-Options nosniff;
        }
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # Bloquear acceso a archivos sensibles
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ ~\$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

# Recargar configuración
log "Recargando configuración de Nginx..."
nginx -t && systemctl reload nginx

# Configurar firewall
log "Configurando firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
fi

# Test SSL
log "Verificando configuración SSL..."
if command -v curl &> /dev/null; then
    if curl -I https://$DOMAIN/health &> /dev/null; then
        log "✅ SSL configurado correctamente"
    else
        warning "SSL configurado pero el servicio no responde"
    fi
fi

# Generar reporte
log "Generando reporte de configuración..."
cat > /tmp/ssl_setup_report.txt << EOF
MCP Enterprise SSL/TLS Setup Report
===================================
Date: $(date)
Domain: $DOMAIN
Email: $EMAIL

SSL Certificate Status:
$(certbot certificates 2>/dev/null || echo "No certificates found")

Nginx Status:
$(systemctl status nginx --no-pager -l)

SSL Test:
$(curl -I https://$DOMAIN/health 2>&1 | head -5 || echo "SSL test failed")

Next Steps:
1. Verify SSL certificate is working: https://$DOMAIN
2. Check SSL rating: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN
3. Monitor certificate expiration
4. Test automatic renewal: certbot renew --dry-run
EOF

log "✅ SSL/TLS setup completado"
log "📄 Reporte guardado en: /tmp/ssl_setup_report.txt"
log "🌐 Sitio disponible en: https://$DOMAIN"

echo ""
echo -e "${GREEN}🎉 SSL/TLS configurado exitosamente!${NC}"
echo "Próximos pasos:"
echo "1. Verificar que el sitio funciona: https://$DOMAIN"
echo "2. Probar renovación automática: certbot renew --dry-run"
echo "3. Configurar monitoreo de certificados"

