######################################################################
# Alternative Dockerfile using official JupyterHub GPU base image
# Use this if the PyTorch base continues to have issues
######################################################################

FROM quay.io/jupyterhub/singleuser:5.4.2

USER root

######################################################################
# Install system packages
######################################################################
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

USER ${NB_UID}

######################################################################
# GPU Deep Learning Libraries
######################################################################

# PyTorch with CUDA 11.8
RUN pip install --no-cache-dir \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# TensorFlow with GPU
RUN pip install --no-cache-dir tensorflow[and-cuda]

# ML/AI libraries
RUN pip install --no-cache-dir \
    transformers \
    datasets \
    accelerate \
    opencv-python-headless

# Data science stack
RUN pip install --no-cache-dir \
    scikit-learn \
    pandas \
    numpy \
    matplotlib \
    seaborn \
    plotly \
    scipy \
    statsmodels

# Git integration
RUN pip install --no-cache-dir \
    jupyterlab-git \
    nbgitpuller

# Ensure work directory exists and has correct permissions
USER root
RUN mkdir -p /home/jovyan/work && \
    chown -R ${NB_UID}:${NB_GID} /home/jovyan/work
USER ${NB_UID}

ENV JUPYTER_ENABLE_LAB=yes
WORKDIR /home/jovyan/work

