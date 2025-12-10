# This is a basic docker image for use in the clinic
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Switch to root to update and install tools
RUN apt-get update && apt-get install -y \
    curl git \
    libspatialindex-dev \
    libgdal-dev \
    libgeos-dev \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*
# Create working directory
WORKDIR /project

COPY pyproject.toml .
COPY uv.lock .

# Resolve and install Python packages from pyproject/uv.lock
RUN /usr/local/bin/uv venv
ENV VIRTUAL_ENV=/project/.venv
ENV PATH="/project/.venv/bin:$PATH"
ENV PYTHONPATH=/project/src

COPY . .
RUN uv sync


# Run Data Preprocessing
RUN python dataprep.py

# Expose Streamlit Port
EXPOSE 8501

CMD ["streamlit", "run", "Homepage.py", "--server.port=8501", "--server.address=0.0.0.0"]