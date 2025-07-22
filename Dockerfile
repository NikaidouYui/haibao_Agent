# Stage 1: Build the frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy package files and install dependencies
COPY hajimiUI/package.json hajimiUI/package-lock.json ./hajimiUI/
RUN cd hajimiUI && npm install

# Copy the rest of the frontend source code
COPY hajimiUI/ ./hajimiUI/

# The vite.config.js outputs to ../app/templates/assets, so we need the app directory structure
# We only need the directory, not the content
RUN mkdir -p app/templates

# Run the build script
RUN cd hajimiUI && npm run build:app

# Stage 2: Setup the Python backend
FROM python:3.12-slim

WORKDIR /app

# Copy Python dependency files and install them
COPY requirements.txt uv.lock pyproject.toml ./
RUN pip install uv
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy the backend application code and other necessary files
COPY app/ ./app/
COPY version.txt ./

# Copy the built frontend assets and index.html from the builder stage
COPY --from=frontend-builder /app/app/templates /app/templates

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]