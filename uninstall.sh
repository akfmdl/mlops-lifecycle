#!/bin/bash

# Exit on error
set -e

echo "============================="
echo "MLOps Lifecycle Uninstallation"
echo "============================="

# Uninstall k3s
echo "Uninstalling k3s..."
if [ -f /usr/local/bin/k3s-uninstall.sh ]; then
    sudo /usr/local/bin/k3s-uninstall.sh
elif [ -f /usr/bin/k3s-uninstall.sh ]; then
    sudo /usr/bin/k3s-uninstall.sh
else
    echo "k3s uninstall script not found. Trying to find it..."
    K3S_PATH=$(which k3s 2>/dev/null || echo "")
    if [ -n "$K3S_PATH" ]; then
        K3S_DIR=$(dirname "$K3S_PATH")
        if [ -f "$K3S_DIR/k3s-uninstall.sh" ]; then
            sudo "$K3S_DIR/k3s-uninstall.sh"
        else
            echo "Warning: k3s uninstall script not found. Please manually remove k3s if needed."
        fi
    else
        echo "Warning: k3s binary not found. It may not be installed."
    fi
fi

# Remove kubectl
echo "Removing kubectl..."
if command -v kubectl &> /dev/null; then
    sudo rm -f $(which kubectl)
    echo "kubectl removed."
else
    echo "kubectl not found. Skipping."
fi

# Remove k9s
echo "Removing k9s..."
if command -v k9s &> /dev/null; then
    sudo rm -f $(which k9s)
    echo "k9s removed."
else
    echo "k9s not found. Skipping."
fi

# Remove helm
echo "Removing helm..."
if command -v helm &> /dev/null; then
    sudo rm -f $(which helm)
    echo "helm removed."
else
    echo "helm not found. Skipping."
fi

# Remove KUBECONFIG from environment files
echo "Removing KUBECONFIG environment variable..."
if [ -f ~/.bashrc ]; then
    sed -i '/export KUBECONFIG=\/etc\/rancher\/k3s\/k3s.yaml/d' ~/.bashrc
fi

if [ -f ~/.zshrc ]; then
    sed -i '/export KUBECONFIG=\/etc\/rancher\/k3s\/k3s.yaml/d' ~/.zshrc
fi

# Remove k3s config
echo "Removing k3s configuration files..."
sudo rm -rf /etc/rancher/k3s 2>/dev/null || true

# Print completion message
echo "========================================"
echo "Uninstallation Complete!"
echo "========================================"
echo "k3s, kubectl, k9s, and helm have been removed."
echo "You may need to restart your shell for all changes to take effect."
echo "========================================" 