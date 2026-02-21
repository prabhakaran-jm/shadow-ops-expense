# Shadow Ops backend – production image for App Runner
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# App Runner sets PORT; default for local runs
ENV PORT=8000
EXPOSE ${PORT}

# Run uvicorn on 0.0.0.0 so it accepts external connections
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
