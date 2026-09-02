FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG FALSE

MAINTAINER https://pavelcode5426.github.io

WORKDIR /code


#RUN apk add --no-cache mariadb-connector-c-dev
#RUN apk update && apk add python3 python3-dev mariadb-dev build-base
#RUN apk add netcat-openbsd
#RUN apk add libgomp

RUN pip install --upgrade pip
RUN  apt-get update && apt-get install -y --no-install-recommends supervisor && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

#RUN apk del python3-dev mariadb-dev build-base
COPY . .
COPY supervisor.conf /etc/supervisor/conf.d/supervisor.conf
COPY entrypoint.sh /entrypoint.sh

EXPOSE 8000
VOLUME ["/code/media"]

CMD ["sh","/entrypoint.sh"]
