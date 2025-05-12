# Use the official Python image as a base
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker's caching
COPY requirements.txt /app/

# Install dependencies *before* copying the full project to prevent reinstalling packages on every code update
RUN pip install --no-cache-dir torch==2.6.0+cpu --index-url https://download.pytorch.org/whl/cpu
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt --index-url https://pypi.python.org/simple/

# Now copy the rest of the application files
COPY . /app

# Expose Streamlit's default port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
