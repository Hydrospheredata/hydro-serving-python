ARG PYTHON_IMAGE_VERSION=latest
FROM python:${PYTHON_IMAGE_VERSION}-slim
ARG GRPC_HEALTH_PROBE_VERSION=v0.4.2

ENV APP_PORT=9091
ENV MODEL_DIR=/model
VOLUME /model
LABEL DEPLOYMENT_TYPE=APP

RUN apt-get update && \
    apt-get -y install wget libgomp1

RUN wget -qO/bin/grpc_health_probe https://github.com/grpc-ecosystem/grpc-health-probe/releases/download/${GRPC_HEALTH_PROBE_VERSION}/grpc_health_probe-linux-amd64 && \
    chmod +x /bin/grpc_health_probe

HEALTHCHECK --start-period=10s CMD /bin/grpc_health_probe -addr=:${APP_PORT}

ADD . /app/

RUN chmod +x /app/src/main.py
RUN sync 

RUN useradd -u 42069 app && \
    mkdir /home/app && \
    chown app /home/app && \
    chown app /app && \
    chmod +x /app/start.sh

USER app

RUN pip install --user -r /app/requirements.txt

WORKDIR /app/src

CMD ["/app/start.sh"]
