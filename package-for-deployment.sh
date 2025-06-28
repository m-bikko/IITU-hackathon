#!/bin/bash

# Package SmartAla for Google Cloud Deployment
# This script creates a deployment package with all necessary files

echo "📦 Packaging SmartAla for deployment..."

# Create deployment package directory
PACKAGE_DIR="smartala-deployment-package"
rm -rf $PACKAGE_DIR
mkdir -p $PACKAGE_DIR

# Copy application files
echo "📁 Copying application files..."
cp app.py $PACKAGE_DIR/
cp requirements.txt $PACKAGE_DIR/
cp Dockerfile $PACKAGE_DIR/
cp docker-compose.yml $PACKAGE_DIR/
cp nginx.conf $PACKAGE_DIR/
cp .dockerignore $PACKAGE_DIR/

# Copy templates and static directories
cp -r templates/ $PACKAGE_DIR/
if [ -d "static" ]; then
    cp -r static/ $PACKAGE_DIR/
fi

# Copy deployment scripts
cp deploy.sh $PACKAGE_DIR/
cp quick-deploy.sh $PACKAGE_DIR/
cp DEPLOYMENT_GUIDE.md $PACKAGE_DIR/

# Make scripts executable
chmod +x $PACKAGE_DIR/*.sh

# Create a simple README for the package
cat > $PACKAGE_DIR/README.md << 'EOF'
# SmartAla Deployment Package

This package contains everything needed to deploy SmartAla on Google Cloud Platform.

## Quick Start

1. Upload this entire folder to your Google Cloud VM
2. SSH into your VM
3. Run: `./quick-deploy.sh`

## Files Included

- `app.py` - Main Flask application
- `templates/` - HTML templates
- `static/` - Static assets (if any)
- `Dockerfile` - Docker container configuration
- `docker-compose.yml` - Multi-container setup
- `nginx.conf` - Nginx reverse proxy configuration
- `requirements.txt` - Python dependencies
- `deploy.sh` - Full deployment script
- `quick-deploy.sh` - Quick deployment script
- `DEPLOYMENT_GUIDE.md` - Complete deployment guide

## Deployment Options

### Option 1: Quick Deploy (Recommended)
```bash
./quick-deploy.sh
```

### Option 2: Manual Deploy
```bash
./deploy.sh
# Then upload files and run docker-compose up -d --build
```

### Option 3: Follow the complete guide
Read `DEPLOYMENT_GUIDE.md` for detailed instructions.

## Support

Check the logs if something goes wrong:
```bash
docker-compose logs -f
```
EOF

# Create the deployment package archive
echo "🗜️ Creating deployment archive..."
tar -czf smartala-deployment.tar.gz $PACKAGE_DIR/

# Get file sizes
PACKAGE_SIZE=$(du -sh $PACKAGE_DIR | cut -f1)
ARCHIVE_SIZE=$(du -sh smartala-deployment.tar.gz | cut -f1)

echo "✅ Deployment package created successfully!"
echo ""
echo "📊 Package Information:"
echo "   Directory: $PACKAGE_DIR ($PACKAGE_SIZE)"
echo "   Archive:   smartala-deployment.tar.gz ($ARCHIVE_SIZE)"
echo ""
echo "📋 Next Steps:"
echo "   1. Upload smartala-deployment.tar.gz to your Google Cloud VM"
echo "   2. Extract: tar -xzf smartala-deployment.tar.gz"
echo "   3. Enter directory: cd $PACKAGE_DIR"
echo "   4. Run: ./quick-deploy.sh"
echo ""
echo "🌐 Upload methods:"
echo "   • Google Cloud Console SSH file upload"
echo "   • SCP: gcloud compute scp smartala-deployment.tar.gz VM_NAME:~/"
echo "   • Git: Push to repository and clone on VM"
echo ""

# List package contents
echo "📁 Package contents:"
find $PACKAGE_DIR -type f | sort 