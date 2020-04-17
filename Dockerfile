ARG PYTHON_IMAGE_VERSION=latest
FROM python:${PYTHON_IMAGE_VERSION}-slim

ENV APP_PORT=9091
ENV MODEL_DIR=/model
LABEL DEPLOYMENT_TYPE=APP

RUN apt-get update

RUN apt-get -y install wget libgomp1

RUN GRPC_HEALTH_PROBE_VERSION=v0.3.1 && \
    wget -qO/bin/grpc_health_probe https://github.com/grpc-ecosystem/grpc-health-probe/releases/download/${GRPC_HEALTH_PROBE_VERSION}/grpc_health_probe-linux-amd64 && \
    chmod +x /bin/grpc_health_probe

HEALTHCHECK --start-period=10s CMD /bin/grpc_health_probe -addr=:${APP_PORT}

ADD . /app/

RUN pip install -r /app/requirements.txt

VOLUME /model

WORKDIR /app/src

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]