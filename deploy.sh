#!/bin/bash

# SmartAla Deployment Script for Google Cloud Platform
# This script automates the deployment of SmartAla navigation system

set -e  # Exit on any error

echo "🚀 Starting SmartAla deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker
print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    # Add Docker's official GPG key
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    
    # Add the repository to Apt sources
    echo \
      "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    print_warning "Please log out and log back in for Docker group changes to take effect"
else
    print_success "Docker is already installed"
fi

# Install Docker Compose (standalone)
print_status "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    print_success "Docker Compose is already installed"
fi

# Install additional tools
print_status "Installing additional tools..."
sudo apt install -y git curl wget htop nano vim ufw

# Configure firewall
print_status "Configuring firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp
print_success "Firewall configured"

# Create application directory
APP_DIR="/home/$USER/smartala"
print_status "Creating application directory: $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# Create necessary directories
mkdir -p audio_uploads logs ssl

# Set proper permissions
chmod 755 audio_uploads logs
chmod 700 ssl

print_status "Creating environment file..."
cat > .env << EOF
# SmartAla Environment Configuration
FLASK_ENV=production
GEMINI_API_KEY=AIzaSyAa6831q1q_61pxjnatffMqWQEMPp9jRjQ
GOOGLE_MAPS_API_KEY=AIzaSyBI_q34br_taffgYVlIs7hQ25yl3QjEXk0
SECRET_KEY=smartala-production-secret-$(openssl rand -hex 16)
EOF

# Create startup script
print_status "Creating startup script..."
cat > start.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting SmartAla services..."

# Pull latest images
docker-compose pull

# Build and start services
docker-compose up -d --build

# Show status
docker-compose ps

echo "✅ SmartAla is now running!"
echo "🌐 Access the application at:"
echo "   HTTP: http://$(curl -s ifconfig.me):80"
echo "   Alternative: http://$(curl -s ifconfig.me):8080"
echo ""
echo "📊 To view logs: docker-compose logs -f"
echo "🔧 To restart: docker-compose restart"
echo "🛑 To stop: docker-compose down"
EOF

chmod +x start.sh

# Create monitoring script
print_status "Creating monitoring script..."
cat > monitor.sh << 'EOF'
#!/bin/bash

echo "📊 SmartAla System Status"
echo "========================="
echo ""

echo "🐳 Docker Containers:"
docker-compose ps
echo ""

echo "💾 System Resources:"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory Usage: $(free | grep Mem | awk '{printf("%.2f%%\n", $3/$2 * 100.0)}')"
echo "Disk Usage: $(df -h / | awk 'NR==2{printf "%s\n", $5}')"
echo ""

echo "🌐 Network Status:"
echo "External IP: $(curl -s ifconfig.me)"
echo "Port 80 Status: $(nc -z localhost 80 && echo "Open" || echo "Closed")"
echo "Port 443 Status: $(nc -z localhost 443 && echo "Open" || echo "Closed")"
echo ""

echo "📝 Recent Logs (last 10 lines):"
docker-compose logs --tail=10 smartala-app
EOF

chmod +x monitor.sh

# Create backup script
print_status "Creating backup script..."
cat > backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/home/$USER/smartala-backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "💾 Creating backup..."

mkdir -p $BACKUP_DIR

# Backup application data
tar -czf "$BACKUP_DIR/smartala_backup_$DATE.tar.gz" \
    audio_uploads/ \
    logs/ \
    .env \
    docker-compose.yml

echo "✅ Backup created: $BACKUP_DIR/smartala_backup_$DATE.tar.gz"

# Keep only last 7 backups
find $BACKUP_DIR -name "smartala_backup_*.tar.gz" -mtime +7 -delete

echo "🧹 Old backups cleaned up"
EOF

chmod +x backup.sh

print_success "Deployment scripts created successfully!"
print_status "Application directory: $APP_DIR"
print_status "Next steps:"
echo "  1. Upload your application files to $APP_DIR"
echo "  2. Run: ./start.sh"
echo "  3. Monitor with: ./monitor.sh"
echo "  4. Backup with: ./backup.sh"

print_warning "IMPORTANT: Please log out and log back in to apply Docker group changes!"

echo ""
print_success "🎉 Deployment preparation completed!" 