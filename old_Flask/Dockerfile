FROM python:3.7

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt

COPY . /app

# Set the environment variable PORT
ENV PORT 8080

# Correcting the CMD to use Flask command, assuming backend.py is your Flask file
CMD ["python", "app.py"]
