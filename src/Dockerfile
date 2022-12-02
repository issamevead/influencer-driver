FROM python:3.9-slim

WORKDIR /src

RUN apt-get update                             \
    && apt-get install -y --no-install-recommends \
    ca-certificates curl firefox-esr           \
    && rm -fr /var/lib/apt/lists/*                \
    && curl -L https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz | tar xz -C /usr/local/bin \
    && apt-get purge -y ca-certificates curl

# RUN apk update && apk add ca-certificates && rm -rf /var/cache/apk/*
# RUN update-ca-certificates

COPY requirements.txt requirements.txt
RUN python3 -m pip install --upgrade pip\
    && pip3 install --no-cache-dir -r requirements.txt

COPY . /src
COPY ./mitm-certs/* /usr/local/share/ca-certificates/

# CMD ["proxychains", "python3", "main.py"]
CMD ["python3", "main.py"]