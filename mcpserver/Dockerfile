ARG VERSION=3.12
FROM python:${VERSION:-3.11}

WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Cài đặt các gói cần thiết cho OpenAI Agent SDK và MCP server
RUN pip install --use-deprecated=legacy-resolver -r requirements.txt

# Mở port 9000 
EXPOSE 9000 

# Command to run the application
CMD ["python", "run.py"]