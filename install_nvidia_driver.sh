#!/bin/bash

# Exit on error
set -e

echo "====================================="
echo "NVIDIA Driver Auto-Installer"
echo "====================================="

# Check if user has root privileges
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root or with sudo privileges."
    exit 1
fi

# Check if nvidia-smi is already installed
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA driver is already installed:"
    nvidia-smi
    read -p "Do you want to reinstall/update the driver? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting without changes."
        exit 0
    fi
fi

# Check OS
if ! command -v apt-get &> /dev/null; then
    echo "This script only supports Debian/Ubuntu systems."
    exit 1
fi

# Install prerequisites
echo "Installing prerequisites..."
apt-get update
apt-get install -y pciutils ubuntu-drivers-common software-properties-common curl wget

# Detect GPU model
echo "Detecting GPU..."
if ! lspci | grep -i nvidia &> /dev/null; then
    echo "No NVIDIA GPU detected. Please check if your GPU is properly installed."
    exit 1
fi

GPU_MODEL=$(lspci | grep -i nvidia | head -n 1 | cut -d ":" -f 3 | xargs)
echo "Detected GPU: $GPU_MODEL"

# Add NVIDIA driver repository
echo "Adding NVIDIA driver repository..."
add-apt-repository -y ppa:graphics-drivers/ppa
apt-get update

# Get recommended driver version
echo "Finding recommended driver version..."
RECOMMENDED_DRIVER=$(ubuntu-drivers devices | grep -i "nvidia-driver-" | grep "recommended" | awk '{print $3}')

# If no recommended driver is found, choose the latest one
if [ -z "$RECOMMENDED_DRIVER" ]; then
    echo "No recommended driver found. Selecting the latest version..."
    RECOMMENDED_DRIVER=$(ubuntu-drivers devices | grep -i "nvidia-driver-" | head -n 1 | awk '{print $3}')
fi

# If still no driver is found, use the default (570)
if [ -z "$RECOMMENDED_DRIVER" ]; then
    echo "No driver detected automatically. Using the default driver (570)."
    RECOMMENDED_DRIVER="nvidia-driver-570"
fi

echo "Installing $RECOMMENDED_DRIVER..."
apt-get install -y $RECOMMENDED_DRIVER

# Install CUDA toolkit if needed (optional)
read -p "Do you want to install CUDA toolkit? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing CUDA toolkit..."
    wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
    dpkg -i cuda-keyring_1.1-1_all.deb
    apt-get update
    apt-get install -y cuda
    echo 'export PATH=/usr/local/cuda/bin:$PATH' >> /etc/profile.d/cuda.sh
    echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> /etc/profile.d/cuda.sh
    rm cuda-keyring_1.1-1_all.deb
fi

# Install NVIDIA Container Toolkit
echo "Installing NVIDIA Container Toolkit..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

apt-get update
apt-get install -y nvidia-container-toolkit nvidia-container-runtime

echo "====================================="
echo "Installation completed!"
echo "====================================="
echo "To verify the installation, run: nvidia-smi"
echo "A reboot is recommended to complete the installation."
echo "Would you like to reboot now?"
read -p "(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    reboot
fi 