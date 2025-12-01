# ==========================================
# Dockerfile
# Author: @natelgrw
# Last Edited: 11/30/2025
#
# A Dockerfile that builds a Docker container
# for FirmaForge.
# ==========================================

# based on Ubuntu 22.04 for maximum compatibility
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# install system dependencies and tools
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    build-essential \
    wget \
    curl \
    git \
    squashfs-tools \
    p7zip-full \
    e2fsprogs \
    binutils \
    file \
    binwalk \
    qemu-system \
    qemu-system-arm \
    qemu-system-mips \
    qemu-system-x86 \
    mtd-utils \
    u-boot-tools \
    genext2fs \
    cpio \
    xxd \
    bsdmainutils \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# install python dependencies
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir \
    click>=8.0.0 \
    pycryptodome>=3.15.0 \
    python-magic>=0.4.27 \
    hexdump>=3.3 \
    pytest>=7.0.0 \
    jefferson \
    ubi_reader

# copy project files
COPY firmaforge/ /app/firmaforge/
COPY demo_firmware/ /app/demo_firmware/

ENV PYTHONPATH=/app

CMD ["/bin/bash"]

