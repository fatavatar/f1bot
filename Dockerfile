FROM python:alpine3.8

ENV GMAIL_PASSWORD=password
ENV GMAIL_USER=email@gmail.com
ENV F1_BASE_URL=yoururl.com
ENV PRODUCTION=0
VOLUME /app/data

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY *.py .
COPY templates templates
CMD ["python3", "-u", "incomming.py"]
