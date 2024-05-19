# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /service_app

COPY . /service_app

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run the plotly dash app.py when the container launches
CMD ["python", "app.py"]
