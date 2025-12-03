######################################################################
# GPU-enabled base image for NVIDIA server
# - Uses official PyTorch CUDA runtime image as a solid GPU foundation
# - We add JupyterLab, TensorFlow, and extra ML libraries on top
######################################################################

FROM pytorch/pytorch:2.3.0-cuda11.8-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive

######################################################################
# System dependencies
######################################################################
USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

######################################################################
# Create a non-root user compatible with JupyterHub defaults
# - Name: jovyan
# - Home: /home/jovyan
######################################################################
RUN useradd -m -s /bin/bash jovyan && \
    chown -R jovyan:jovyan /home/jovyan

USER jovyan
WORKDIR /home/jovyan

######################################################################
# Python / ML stack
# - PyTorch is already included from the base image
# - We add TensorFlow GPU, Transformers, etc.
######################################################################

# Upgrade pip first to avoid dependency resolution issues
RUN pip install --no-cache-dir --upgrade pip

# TensorFlow with GPU support
RUN pip install --no-cache-dir tensorflow[and-cuda]

# Additional ML/AI libraries
RUN pip install --no-cache-dir \
    transformers \
    datasets \
    accelerate \
    opencv-python-headless

######################################################################
# Jupyter stack
# CRITICAL: jupyterhub package provides jupyterhub-singleuser command
######################################################################
RUN pip install --no-cache-dir \
    jupyterhub \
    jupyterlab \
    notebook \
    jupyterlab-git

ENV JUPYTER_ENABLE_LAB=yes

# Default working directory for notebooks
WORKDIR /home/jovyan/work

