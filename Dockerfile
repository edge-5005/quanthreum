# =====================================================================
# Quanthreum (QTH) - Production Dockerfile
# Native Post-Quantum Blockchain Node & Web3 Portal
# =====================================================================

FROM python:3.12-slim

# Create non-root user for security
RUN groupadd -r quanthreum && useradd -r -g quanthreum -m -d /home/quanthreum quanthreum

WORKDIR /app

# Copy codebase
COPY quanthreum/ /app/quanthreum/
COPY contracts/ /app/contracts/
COPY web/ /app/web/
COPY quanthreum_cli.py /app/
COPY README.md /app/

# Create persistent storage volume
RUN mkdir -p /data && chown -R quanthreum:quanthreum /app /data

USER quanthreum

# Expose Quanthreum Node Web UI & REST RPC Port
EXPOSE 8545

# Healthcheck
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8545/api/info', timeout=2)" || exit 1

# Start the full node (listening on 0.0.0.0 to accept external requests)
CMD ["python", "quanthreum_cli.py", "node", "start", "--host", "0.0.0.0", "--port", "8545", "--dir", "/data"]
