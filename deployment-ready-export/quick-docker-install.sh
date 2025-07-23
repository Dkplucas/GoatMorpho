#!/bin/bash

echo "🐳 Installing Docker on Ubuntu Server..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index
sudo apt update

# Install Docker
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add current user to docker group
sudo usermod -aG docker $USER

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

echo "✅ Docker installation completed!"
echo "🔄 Please log out and log back in (or run 'newgrp docker') to use Docker without sudo"

# Test Docker installation
echo "🧪 Testing Docker installation..."
if sudo docker run hello-world; then
    echo "✅ Docker is working correctly!"
else
    echo "❌ Docker test failed. Please check the installation."
fi

echo ""
echo "📋 Next steps:"
echo "1. Log out and log back in"
echo "2. Run: ./docker-deploy.sh"