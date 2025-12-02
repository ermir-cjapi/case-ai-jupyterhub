FROM jupyter/minimal-notebook:python-3.11

USER root

# System dependencies (add cluster-specific CUDA/NVIDIA drivers outside the image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

USER ${NB_UID}

# Core Python libraries for data science / ML experiments
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    scipy \
    scikit-learn \
    matplotlib \
    seaborn \
    jupyterlab \
    ipywidgets

# Uncomment and adjust if you want GPU frameworks in V1
# RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

ENV JUPYTER_ENABLE_LAB=yes


