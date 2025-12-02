FROM jupyter/minimal-notebook:python-3.11

USER root

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    curl \
    wget \
    vim \
  && rm -rf /var/lib/apt/lists/*

USER ${NB_UID}

# Core data science libraries (like scipy-notebook)
RUN python -m pip install --no-cache-dir \
    numpy \
    pandas \
    scipy \
    scikit-learn \
    matplotlib \
    seaborn \
    plotly \
    jupyterlab \
    ipywidgets \
    notebook

# Deep Learning with GPU support
# PyTorch with CUDA 11.8 support
RUN python -m pip install --no-cache-dir \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# TensorFlow with GPU support
RUN python -m pip install --no-cache-dir \
    tensorflow[and-cuda]

# Additional ML/AI libraries
RUN python -m pip install --no-cache-dir \
    transformers \
    datasets \
    accelerate \
    opencv-python-headless \
    pillow

# Data processing
RUN python -m pip install --no-cache-dir \
    h5py \
    pytables \
    sqlalchemy \
    openpyxl

# Jupyter extensions
RUN python -m pip install --no-cache-dir \
    jupyterlab-git \
    ipympl

ENV JUPYTER_ENABLE_LAB=yes
