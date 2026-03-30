FROM python:3.13.0rc1-bookworm

WORKDIR /app

# Install necessary tools and Rust
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add Rust and Cargo to the PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Generate SSL certificates
# Generate SSL certificates only if they don't exist
RUN if [ ! -f /app/cert.pem ]; then \
        openssl req -x509 -newkey rsa:4096 -keyout /app/key.pem -out /app/cert.pem -days 365 -nodes -subj "/CN=localhost"; \
    fi

COPY requirements.txt /app/

COPY src /app/

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "Flask_GUI.py"]