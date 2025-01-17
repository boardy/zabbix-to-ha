# Use an official Python runtime as the base image
FROM python:alpine3.13

# Set the working directory in the container to /app
WORKDIR /app

ADD . .

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Run your script when the container launches
CMD ["python3", "main.py"]