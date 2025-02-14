FROM python:3.13.2-bookworm

RUN apt update && apt upgrade -y
COPY requirements.txt /tmp
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt
RUN mkdir /app
WORKDIR /app
COPY src/ /app

CMD ["python3", "main.py"]