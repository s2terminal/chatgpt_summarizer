FROM python:3.10-slim AS builder
WORKDIR /app
ENV PYTHONPATH="/app:$PYTHONPATH"

RUN apt-get update && apt-get install -y \
    build-essential \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN pip install poetry
RUN poetry config virtualenvs.create false

COPY pyproject.toml ./
COPY poetry.lock ./
RUN poetry install --without dev

CMD ["poetry", "run", "streamlit", "run", "src/chatgpt_summarizer/main.py", "--server.port", "8080"]

FROM builder AS dev

RUN apt-get update && apt-get install -y \
    git \
    curl
RUN git config --global --add safe.directory /app

RUN poetry install

FROM builder AS prod
COPY ./src /app/src
