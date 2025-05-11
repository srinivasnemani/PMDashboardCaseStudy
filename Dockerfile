FROM python:3.11-slim

# Create a directory called 'app' inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    glpk-utils \
    libglpk-dev \
    build-essential \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy only the necessary directories
COPY src/ /app/src/
COPY dbs/ /app/dbs/
COPY .streamlit/ /app/.streamlit/

# Set Python path properly
ENV PYTHONPATH="/app"

# Expose the port that Streamlit runs on
EXPOSE 8501

# Set the working directory to ensure we're in the right place
WORKDIR /app

# Add a more lenient healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the Streamlit app with debug logging and proper configuration
CMD ["streamlit", "run", \
     "src/visualizations/Back_Test_Dashboard.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--logger.level=debug", \
     "--server.headless=true", \
     "--browser.serverAddress=localhost", \
     "--browser.serverPort=8501", \
     "--theme.base=light"]
