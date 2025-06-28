# 🚀 SmartAla Deployment Guide for Google Cloud Platform

This guide provides complete step-by-step instructions for deploying the SmartAla navigation system on Google Cloud Platform using Ubuntu 22.04.

## 📋 Prerequisites

- Google Cloud Platform account
- Basic knowledge of SSH and Linux commands
- Your application files ready for upload

## 🌥️ Part 1: Setting Up Google Cloud VM

### Step 1: Create a VM Instance

1. **Login to Google Cloud Console**
   - Go to [console.cloud.google.com](https://console.cloud.google.com)
   - Select or create a project

2. **Navigate to Compute Engine**
   - Go to `Compute Engine` > `VM instances`
   - Click `CREATE INSTANCE`

3. **Configure VM Instance**
   ```
   Name: smartala-server
   Region: us-central1 (or closest to your users)
   Zone: us-central1-a
   Machine type: e2-medium (2 vCPU, 4 GB memory) - minimum recommended
   ```

4. **Boot Disk Configuration**
   ```
   Operating System: Ubuntu
   Version: Ubuntu 22.04 LTS
   Boot disk type: Standard persistent disk
   Size: 20 GB (minimum)
   ```

5. **Firewall Settings**
   - ✅ Allow HTTP traffic
   - ✅ Allow HTTPS traffic

6. **Click CREATE**

### Step 2: Configure Firewall Rules

1. **Go to VPC Network > Firewall**
2. **Create firewall rule for custom ports:**
   ```
   Name: smartala-ports
   Direction: Ingress
   Action: Allow
   Targets: All instances in the network
   Source IP ranges: 0.0.0.0/0
   Protocols and ports: 
   - TCP: 80, 443, 8080
   ```

### Step 3: Reserve Static IP (Optional but Recommended)

1. **Go to VPC Network > External IP addresses**
2. **Click RESERVE STATIC ADDRESS**
   ```
   Name: smartala-static-ip
   Type: Regional
   Region: (same as your VM)
   ```
3. **Assign to your VM instance**

## 🔧 Part 2: Initial Server Setup

### Step 1: Connect to Your VM

1. **From Google Cloud Console:**
   - Go to `Compute Engine` > `VM instances`
   - Click `SSH` next to your instance

2. **Or use gcloud CLI:**
   ```bash
   gcloud compute ssh smartala-server --zone=us-central1-a
   ```

### Step 2: Update System and Create User (if needed)

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Create a non-root user (if not already exists)
sudo adduser smartala
sudo usermod -aG sudo smartala

# Switch to the new user
su - smartala
```

## 📦 Part 3: Automated Deployment

### Step 1: Download and Run Deployment Script

```bash
# Download the deployment script
curl -O https://raw.githubusercontent.com/your-repo/smartala/main/deploy.sh

# Make it executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

**The script will automatically:**
- Install Docker and Docker Compose
- Configure firewall
- Create application directories
- Set up monitoring and backup scripts

### Step 2: Log Out and Back In

```bash
# Log out to apply Docker group changes
exit

# Log back in via SSH
```

## 📁 Part 4: Upload Application Files

### Method 1: Using SCP (from your local machine)

```bash
# Create a tar file of your project (on your local machine)
tar -czf smartala.tar.gz \
    app.py \
    requirements.txt \
    Dockerfile \
    docker-compose.yml \
    nginx.conf \
    templates/ \
    static/ \
    --exclude=__pycache__ \
    --exclude=*.pyc \
    --exclude=.git

# Upload to server
gcloud compute scp smartala.tar.gz smartala-server:~/smartala/ --zone=us-central1-a

# Extract on server
ssh smartala-server
cd ~/smartala
tar -xzf smartala.tar.gz
rm smartala.tar.gz
```

### Method 2: Using Git (if your code is in a repository)

```bash
# On the server
cd ~/smartala

# Clone your repository
git clone https://github.com/your-username/smartala.git .

# Or if you have the files locally, you can use git to push them first
```

### Method 3: Manual File Upload via Console

1. **From Google Cloud Console:**
   - Go to your VM instance
   - Click `SSH`
   - Use the upload button in the SSH window

## 🚀 Part 5: Deploy the Application

### Step 1: Start the Application

```bash
# Navigate to application directory
cd ~/smartala

# Start the services
./start.sh
```

### Step 2: Verify Deployment

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f

# Check system status
./monitor.sh
```

### Step 3: Test the Application

1. **Get your server's external IP:**
   ```bash
   curl ifconfig.me
   ```

2. **Access the application:**
   - Main site: `http://YOUR_IP:80`
   - Alternative: `http://YOUR_IP:8080`
   - Health check: `http://YOUR_IP:80/health`

## 🔒 Part 6: Security and SSL Setup (Optional)

### Step 1: Install Certbot for SSL

```bash
# Install Certbot
sudo apt install -y certbot

# Get SSL certificate (replace your-domain.com)
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to application directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ~/smartala/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ~/smartala/ssl/key.pem
sudo chown smartala:smartala ~/smartala/ssl/*.pem
```

### Step 2: Update Nginx Configuration

```bash
# Edit nginx.conf to enable SSL
nano ~/smartala/nginx.conf

# Uncomment SSL configuration lines
# Update server_name with your domain

# Restart services
docker-compose restart nginx
```

## 📊 Part 7: Monitoring and Maintenance

### Daily Monitoring Commands

```bash
# Check system status
./monitor.sh

# View live logs
docker-compose logs -f smartala-app

# Check resource usage
htop

# View disk usage
df -h
```

### Backup and Restore

```bash
# Create backup
./backup.sh

# View backups
ls -la ~/smartala-backups/

# Restore from backup (if needed)
cd ~/smartala
tar -xzf ~/smartala-backups/smartala_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Update Application

```bash
# Pull latest changes (if using git)
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Or use the start script
./start.sh
```

## 🔧 Part 8: Troubleshooting

### Common Issues and Solutions

1. **Port already in use:**
   ```bash
   # Check what's using the port
   sudo netstat -tulpn | grep :80
   
   # Kill the process or change port in docker-compose.yml
   ```

2. **Docker permission denied:**
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER
   # Log out and back in
   ```

3. **Container won't start:**
   ```bash
   # Check logs
   docker-compose logs smartala-app
   
   # Check if all files are present
   ls -la
   ```

4. **Application not accessible:**
   ```bash
   # Check firewall
   sudo ufw status
   
   # Check if containers are running
   docker-compose ps
   
   # Test locally
   curl localhost:80
   ```

### Performance Optimization

1. **For high traffic, upgrade VM:**
   ```
   Machine type: e2-standard-2 (2 vCPU, 8 GB)
   or higher
   ```

2. **Enable Docker logging limits:**
   ```bash
   # Edit docker-compose.yml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

## 📞 Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly:**
   - Run `./backup.sh`
   - Check `./monitor.sh`
   - Update system: `sudo apt update && sudo apt upgrade`

2. **Monthly:**
   - Review logs for errors
   - Check disk space
   - Update SSL certificates (if using Let's Encrypt)

### Log Locations

- Application logs: `docker-compose logs smartala-app`
- Nginx logs: `docker-compose logs smartala-nginx`
- System logs: `/var/log/syslog`

### Useful Commands

```bash
# Restart specific service
docker-compose restart smartala-app

# View container resource usage
docker stats

# Access container shell
docker-compose exec smartala-app /bin/bash

# Update single container
docker-compose up -d --no-deps smartala-app
```

## 🎉 Conclusion

Your SmartAla navigation system should now be running successfully on Google Cloud Platform! 

**Access URLs:**
- Main application: `http://YOUR_SERVER_IP:80`
- Alternative port: `http://YOUR_SERVER_IP:8080`
- Health check: `http://YOUR_SERVER_IP:80/health`

**Next Steps:**
1. Test all features thoroughly
2. Set up domain name and SSL (optional)
3. Configure monitoring alerts
4. Set up automated backups
5. Document any customizations

For support or issues, check the troubleshooting section or review the application logs using `docker-compose logs -f`.

---

**Security Note:** This deployment is configured for development/testing. For production use, consider:
- Setting up SSL certificates
- Implementing proper authentication
- Using a managed database
- Setting up log aggregation
- Implementing monitoring and alerting 