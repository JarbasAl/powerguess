FROM python:3.11-slim

# powerstat gives live RAPL/battery wattage when run with privileges; dmidecode
# helps identify x86 hardware. Both are optional — without them powerguess falls
# back to a per-model CPU-load estimate.
RUN apt-get update && apt-get install -y --no-install-recommends \
    powerstat \
    dmidecode \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY powerguess/ ./powerguess/

RUN pip install --no-cache-dir -e .

CMD ["python", "-m", "powerguess"]
