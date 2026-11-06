FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .

ENV PATH=/usr/local/bin:$PATH
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

RUN groupadd -g 1000 appuser \
    && useradd -u 1000 -g 1000 -m -s /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
