#!/bin/bash

# Quick Deploy Script for SmartAla on Google Cloud Platform
# This script combines all deployment steps into one command

set -e

echo "🚀 SmartAla Quick Deploy Script"
echo "==============================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Google Cloud
if ! curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/name &>/dev/null; then
    print_error "This script is designed to run on Google Cloud Platform VMs"
    exit 1
fi

print_step "Updating system packages..."
sudo apt update && sudo apt upgrade -y

print_step "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

print_step "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

print_step "Installing additional tools..."
sudo apt install -y git curl wget htop nano ufw netcat

print_step "Configuring firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp

print_step "Creating application directory..."
APP_DIR="/home/$USER/smartala"
mkdir -p $APP_DIR
cd $APP_DIR

# Create all necessary files
print_step "Creating Docker configuration..."

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p audio_uploads logs

ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 5002

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5002/ || exit 1

CMD ["python", "app.py"]
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
Flask==3.0.0
google-generativeai==0.3.2
python-dotenv==1.0.0
Werkzeug==3.0.1
gunicorn==21.2.0
requests==2.31.0
EOF

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  smartala-app:
    build: .
    container_name: smartala-navigation
    ports:
      - "80:5002"
      - "8080:5002"
    environment:
      - FLASK_ENV=production
      - GEMINI_API_KEY=AIzaSyAa6831q1q_61pxjnatffMqWQEMPp9jRjQ
      - GOOGLE_MAPS_API_KEY=AIzaSyBI_q34br_taffgYVlIs7hQ25yl3QjEXk0
    volumes:
      - ./audio_uploads:/app/audio_uploads
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5002/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
EOF

# Create directories
mkdir -p audio_uploads logs templates static
chmod 755 audio_uploads logs

print_step "Application files need to be uploaded..."
print_step "Please upload your application files (app.py, templates/, static/) to:"
echo "   $APP_DIR"
echo ""
echo "You can upload files using one of these methods:"
echo "1. Use the SSH file upload button in Google Cloud Console"
echo "2. Use SCP from your local machine:"
echo "   gcloud compute scp --recurse /path/to/your/app/* VM_NAME:~/smartala/"
echo "3. Use git clone if your code is in a repository"
echo ""
read -p "Press Enter when you have uploaded all application files..."

# Check if required files exist
if [ ! -f "app.py" ]; then
    print_error "app.py not found! Please upload your application files first."
    exit 1
fi

if [ ! -d "templates" ]; then
    print_error "templates/ directory not found! Please upload your application files first."
    exit 1
fi

print_step "Building and starting the application..."
docker-compose up -d --build

print_step "Waiting for application to start..."
sleep 30

print_step "Checking application status..."
if docker-compose ps | grep -q "Up"; then
    print_success "Application is running!"
    
    # Get external IP
    EXTERNAL_IP=$(curl -s ifconfig.me)
    
    echo ""
    echo "🎉 SmartAla is now deployed and running!"
    echo "========================================"
    echo ""
    echo "🌐 Access your application at:"
    echo "   Primary:    http://$EXTERNAL_IP:80"
    echo "   Secondary:  http://$EXTERNAL_IP:8080"
    echo "   Health:     http://$EXTERNAL_IP:80/health"
    echo ""
    echo "📊 Management commands:"
    echo "   Status:     docker-compose ps"
    echo "   Logs:       docker-compose logs -f"
    echo "   Restart:    docker-compose restart"
    echo "   Stop:       docker-compose down"
    echo "   Update:     docker-compose up -d --build"
    echo ""
    echo "📁 Application directory: $APP_DIR"
    echo ""
    
    # Test the application
    if curl -s "http://localhost:80/health" | grep -q "healthy"; then
        print_success "Health check passed!"
    else
        print_error "Health check failed. Check logs with: docker-compose logs"
    fi
    
else
    print_error "Application failed to start. Check logs with: docker-compose logs"
    exit 1
fi

print_success "Deployment completed successfully!"

# Create management scripts
cat > manage.sh << 'EOF'
#!/bin/bash

case $1 in
    start)
        docker-compose up -d
        ;;
    stop)
        docker-compose down
        ;;
    restart)
        docker-compose restart
        ;;
    logs)
        docker-compose logs -f
        ;;
    status)
        docker-compose ps
        echo ""
        echo "External IP: $(curl -s ifconfig.me)"
        echo "Health: $(curl -s http://localhost:80/health || echo 'Failed')"
        ;;
    update)
        docker-compose down
        docker-compose up -d --build
        ;;
    backup)
        mkdir -p ../smartala-backups
        tar -czf "../smartala-backups/backup-$(date +%Y%m%d_%H%M%S).tar.gz" \
            audio_uploads/ logs/ .env docker-compose.yml
        echo "Backup created in ../smartala-backups/"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|status|update|backup}"
        ;;
esac
EOF

chmod +x manage.sh

echo ""
echo "📋 Quick management:"
echo "   ./manage.sh status    - Check status"
echo "   ./manage.sh logs      - View logs"
echo "   ./manage.sh restart   - Restart app"
echo "   ./manage.sh backup    - Create backup"
echo ""

print_success "🎉 SmartAla deployment completed!" 