FROM python:3.10.12

# Set the working directory in the container
WORKDIR /app

# Copy the application code into the container
COPY . /app

# Install any dependencies (if needed)
RUN pip3 install -r requirements.txt
RUN pip3 install requests
RUN pip3 install spacy && python3 -m spacy download en

# Expose port 5000
EXPOSE 5000

# Command to run your Python application
CMD ["python3", "api.py"]
