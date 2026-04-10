#!/bin/bash
set -e

echo "=== GoVision Dependency Installer ==="
echo ""

# System update
echo "[1/4] Updating package lists..."
sudo apt update

# System packages
echo "[2/4] Installing system packages..."
sudo apt install -y \
  python3-picamera2 \
  python3-opencv \
  python3-numpy \
  python3-flask \
  python3-pip \
  python3-yaml \
  libcamera-apps \
  libjpeg-dev \
  avahi-daemon

# Python packages not available via apt
echo "[3/4] Installing Python packages via pip..."
pip install --break-system-packages \
  sgfmill \
  tflite-runtime

# Project directory
echo "[4/4] Setting up project directory..."
mkdir -p ~/govision/cal_images
mkdir -p ~/govision/scans

echo ""
echo "=== Installation complete ==="
echo "Versions installed:"
python3 -c "import cv2; print(f'  OpenCV:  {cv2.__version__}')"
python3 -c "import numpy; print(f'  NumPy:   {numpy.__version__}')"
python3 -c "import flask; print(f'  Flask:   {flask.__version__}')"
python3 -c "from picamera2 import Picamera2; print('  picamera2: ok')"
echo ""
echo "Run 'cd ~/govision' to get started."
