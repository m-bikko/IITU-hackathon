# 🚀 Manual SmartAla Deployment Commands

Deploy SmartAla step-by-step using individual commands with your GitHub repository.

## 📋 Prerequisites
- Google Cloud Platform VM with Ubuntu 22.04
- SSH access to your VM

## 🔧 Step-by-Step Commands

### 1. Update System
```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Docker
```bash
# Add Docker's official GPG key
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add repository
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 3. Add User to Docker Group
```bash
sudo usermod -aG docker $USER
```

### 4. Install Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 5. Install Additional Tools
```bash
sudo apt install -y git curl wget htop nano ufw netcat
```

### 6. Configure Firewall
```bash
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp
```

### 7. Clone Your Repository
```bash
cd ~
git clone https://github.com/m-bikko/IITU-hackathon.git smartala
cd smartala
```

### 8. Create Required Directories
```bash
mkdir -p audio_uploads logs ssl
chmod 755 audio_uploads logs
chmod 700 ssl
```

### 9. Log Out and Back In (for Docker group changes)
```bash
exit
# SSH back into your VM
```

### 10. Build and Start Application
```bash
cd ~/smartala
docker-compose up -d --build
```

### 11. Check Status
```bash
docker-compose ps
```

### 12. View Logs
```bash
docker-compose logs -f
```

### 13. Test Application
```bash
# Get your external IP
curl ifconfig.me

# Test health endpoint
curl http://localhost:80/health
```

## 🌐 Access Your Application

After successful deployment:
- Primary: `http://YOUR_IP:80`
- Secondary: `http://YOUR_IP:8080`
- Health check: `http://YOUR_IP:80/health`

## 📊 Management Commands

### View Status
```bash
docker-compose ps
```

### View Logs
```bash
docker-compose logs -f smartala-app
```

### Restart Application
```bash
docker-compose restart
```

### Stop Application
```bash
docker-compose down
```

### Update Application (pull latest from GitHub)
```bash
git pull origin main
docker-compose down
docker-compose up -d --build
```

### Create Backup
```bash
mkdir -p ~/backups
tar -czf ~/backups/smartala-backup-$(date +%Y%m%d_%H%M%S).tar.gz audio_uploads/ logs/ .env
```

## 🔍 Troubleshooting

### Check if containers are running
```bash
docker ps
```

### Check container logs
```bash
docker logs smartala-navigation
```

### Check disk space
```bash
df -h
```

### Check memory usage
```bash
free -h
```

### Restart Docker service
```bash
sudo systemctl restart docker
```

### Check firewall status
```bash
sudo ufw status
```

### Test local connectivity
```bash
curl localhost:80
```

## 🚨 Common Issues

### Port already in use
```bash
# Check what's using port 80
sudo netstat -tulpn | grep :80
# Kill process if needed
sudo kill -9 PID_NUMBER
```

### Docker permission denied
```bash
# Make sure you logged out and back in after adding to docker group
# Or run with sudo (not recommended)
```

### Application not accessible
```bash
# Check if containers are running
docker-compose ps
# Check firewall
sudo ufw status
# Check logs
docker-compose logs
```

That's it! Your SmartAla application should now be running on Google Cloud Platform. 