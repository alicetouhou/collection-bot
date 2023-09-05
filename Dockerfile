# syntax=docker/dockerfile:1
   
FROM python:3.11-slim

ARG VERSION_TAG
ENV VERSION=$VERSION_TAG

# Copy files for poetry
COPY requirements.txt /app/requirements.txt

# Download dependencies
WORKDIR /app/
RUN pip install -r requirements.txt

# Copy source code
COPY bot/ /app/bot

CMD ["python", "-OO", "-m", "bot"]
