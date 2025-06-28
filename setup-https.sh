#!/bin/bash

# Быстрая настройка HTTPS для SmartAla с самоподписанным сертификатом

echo "🔒 Настройка HTTPS для SmartAla..."

# Создание SSL директории
mkdir -p ssl
cd ssl

# Генерация приватного ключа
echo "🔑 Создание приватного ключа..."
openssl genrsa -out key.pem 2048

# Создание самоподписанного сертификата
echo "📜 Создание SSL сертификата..."
openssl req -new -x509 -key key.pem -out cert.pem -days 365 \
    -subj "/C=KZ/ST=Almaty/L=Almaty/O=SmartAla/OU=Navigation/CN=localhost"

# Установка прав доступа
chmod 600 *.pem

cd ..

# Обновление nginx.conf для HTTPS
echo "⚙️ Обновление конфигурации Nginx..."

# Создание резервной копии
cp nginx.conf nginx.conf.backup

# Обновление конфигурации
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream smartala_backend {
        server smartala-app:5002;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=uploads:10m rate=5r/s;

    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 10M;

    # MIME types
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
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

    # HTTP server (redirect to HTTPS)
    server {
        listen 80;
        server_name _;

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name _;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_session_timeout 1d;
        ssl_session_cache shared:MozTLS:10m;
        ssl_session_tickets off;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=63072000" always;

        # Main application
        location / {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://smartala_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Special handling for audio uploads
        location /send_navigation_audio {
            limit_req zone=uploads burst=10 nodelay;
            
            proxy_pass http://smartala_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
            
            # Longer timeout for audio processing
            proxy_connect_timeout 120s;
            proxy_send_timeout 120s;
            proxy_read_timeout 120s;
        }

        # Static files caching
        location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            proxy_pass http://smartala_backend;
            proxy_set_header Host $host;
        }
    }
}
EOF

echo "🐳 Перезапуск Docker контейнеров..."
docker-compose down
docker-compose up -d --build

echo ""
echo "✅ HTTPS настроен успешно!"
echo ""
echo "🌐 Ваше приложение теперь доступно по адресам:"
echo "   HTTPS: https://$(curl -s ifconfig.me):443"
echo "   HTTP:  http://$(curl -s ifconfig.me):80 (автоматический редирект на HTTPS)"
echo ""
echo "⚠️  ВНИМАНИЕ: Используется самоподписанный сертификат!"
echo "   Браузер покажет предупреждение о безопасности."
echo "   Нажмите 'Дополнительно' → 'Перейти на сайт' для продолжения."
echo ""
echo "🔍 Проверка статуса:"
echo "   docker-compose ps"
echo "   docker-compose logs nginx"
echo ""
echo "📋 Для продакшена используйте Let's Encrypt сертификаты!"
echo "   См. подробности в HTTPS_SETUP.md" 