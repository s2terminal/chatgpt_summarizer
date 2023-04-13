FROM python:3.10-slim
WORKDIR /app
ENV PYTHONPATH="/app:$PYTHONPATH"

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN git config --global --add safe.directory /app

RUN pip install poetry
RUN poetry config virtualenvs.create false

COPY pyproject.toml ./
COPY poetry.lock ./
RUN poetry install

CMD ["poetry", "run", "streamlit", "run", "src/chatgpt_summarizer/main.py", "--server.port", "8080"]
