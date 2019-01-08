FROM ubuntu:14.04

RUN \
  sed -i 's/# \(.*multiverse$\)/\1/g' /etc/apt/sources.list && \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y software-properties-common && \
  apt-get install -y python-dev python-psycopg2 libjpeg-dev zlib1g-dev python-pip curl unzip vim && \
  rm -rf /var/lib/apt/lists/*

ADD ./colleague-api /root/api

ENV HOME /root/api

WORKDIR /root/api

RUN pip install -r requirements.txt

COPY ./entrypoint.sh /root/api/entrypoint.sh
COPY ./dysms_python /root/api/dysms
RUN cd /root/api/dysms/; python setup.py install 


ENTRYPOINT ["/root/api/entrypoint.sh"]
