# Use scipy-notebook which already includes numpy, pandas, scipy, matplotlib, etc.
FROM jupyter/scipy-notebook:latest

# Override SHELL to use sh instead of bash to avoid libtinfo issues
SHELL ["/bin/sh", "-c"]

USER root

# System dependencies for additional packages
RUN apt-get update && apt-get install -y --no-install-recommends git vim && rm -rf /var/lib/apt/lists/*

USER ${NB_UID}

# Additional data science libraries not in scipy-notebook
RUN /opt/conda/bin/pip install --no-cache-dir seaborn plotly ipywidgets

# Deep Learning with GPU support - PyTorch with CUDA 11.8 support
RUN /opt/conda/bin/pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# TensorFlow with GPU support
RUN /opt/conda/bin/pip install --no-cache-dir tensorflow[and-cuda]

# Additional ML/AI libraries
RUN /opt/conda/bin/pip install --no-cache-dir transformers datasets accelerate opencv-python-headless pillow

# Data processing
RUN /opt/conda/bin/pip install --no-cache-dir h5py pytables sqlalchemy openpyxl

# Jupyter extensions
RUN /opt/conda/bin/pip install --no-cache-dir jupyterlab-git ipympl

ENV JUPYTER_ENABLE_LAB=yes

# Set working directory
WORKDIR /home/${NB_USER}
