#!/bin/bash

# Simple clone and setup script for SmartAla
echo "🚀 Cloning SmartAla from GitHub..."

# Clone repository
cd ~
git clone https://github.com/m-bikko/IITU-hackathon.git smartala
cd smartala

# Create required directories
echo "📁 Creating required directories..."
mkdir -p audio_uploads logs ssl
chmod 755 audio_uploads logs
chmod 700 ssl

echo "✅ Repository cloned and directories created!"
echo ""
echo "📍 Location: ~/smartala"
echo ""
echo "🔄 Next steps:"
echo "1. Make sure Docker is installed and you're in the docker group"
echo "2. Run: docker-compose up -d --build"
echo "3. Check status: docker-compose ps"
echo ""
echo "📖 For complete setup instructions, see MANUAL_DEPLOYMENT.md" 