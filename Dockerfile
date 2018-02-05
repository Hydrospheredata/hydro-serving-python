ARG PYTHON_IMAGE_VERSION=latest
FROM python:${PYTHON_IMAGE_VERSION}-alpine

ADD . /app/

RUN pip install -r app/requirements.txt

ENV APP_PORT=9090
ENV SIDECAR_PORT=8080
ENV SIDECAR_HOST=localhost
ENV MODEL_DIR=/model

LABEL DEPLOYMENT_TYPE=APP

VOLUME /model

WORKDIR /app/src

CMD ["/app/start.sh"]