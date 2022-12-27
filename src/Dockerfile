FROM python:3.9

WORKDIR /src

RUN apt-get update
RUN apt-get install proxychains-ng -y

RUN apt-get install -y --no-install-recommends \
    ca-certificates curl firefox-esr           \
    && rm -fr /var/lib/apt/lists/*                \
    && curl -L https://github.com/mozilla/geckodriver/releases/download/v0.32.0/geckodriver-v0.32.0-linux64.tar.gz | tar xz -C /usr/local/bin \
    && apt-get purge -y ca-certificates

# RUN apk update && apk add ca-certificates && rm -rf /var/cache/apk/*
# RUN update-ca-certificates

# Install proxychains
# RUN apt-get install tor
# RUN service tor start

RUN apt-get update && apt install tzdata -y

RUN dpkg-reconfigure -f noninteractive tzdata

# RUN apt-get update && apt-get install -y ntpdate
# RUN ntpdate -v pool.ntp.org

COPY requirements.txt requirements.txt

RUN python3 -m pip install --upgrade pip\
    && pip3 install --no-cache-dir -r requirements.txt

COPY . /src
COPY ./mitm-certs/* /usr/local/share/ca-certificates/

# RUN chmod 777 /etc/proxychains.conf

# CMD ["proxychains", "python3", "main.py"]
CMD ["python3", "preloader.py"]