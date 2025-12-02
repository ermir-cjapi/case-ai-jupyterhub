FROM jupyter/scipy-notebook:2024-12-02

USER root

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends git vim && rm -rf /var/lib/apt/lists/*

USER ${NB_UID}

# Deep Learning with GPU support - PyTorch with CUDA 11.8
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# TensorFlow with GPU support  
RUN pip install --no-cache-dir tensorflow[and-cuda]

# Additional ML/AI libraries
RUN pip install --no-cache-dir transformers datasets accelerate opencv-python-headless

# Jupyter extensions
RUN pip install --no-cache-dir jupyterlab-git

ENV JUPYTER_ENABLE_LAB=yes

WORKDIR /home/${NB_USER}
