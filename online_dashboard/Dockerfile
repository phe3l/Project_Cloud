# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /dashboard_app

# Copy the requirements.txt file first to leverage Docker cache
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run the plotly dash app.py when the container launches
CMD ["python", "app.py"]
