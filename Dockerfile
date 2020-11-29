FROM python:3.8.6-buster

# Making working directory
WORKDIR /server

# Python dependencies
COPY dependencies.txt ./
RUN pip install -r dependencies.txt

# Copy src code
COPY server.py config.json ./

# Expose port 5000
EXPOSE 5000

# Server run command
CMD [ "python", "server.py" ]