FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .

RUN mkdir -p /data
ENV MODEL_PROV_DIR=/data

ENTRYPOINT ["model-prov", "--dir", "/data"]
CMD ["--help"]
