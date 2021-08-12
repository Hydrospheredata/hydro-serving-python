ARG PYTHON_IMAGE_VERSION=latest
FROM python:${PYTHON_IMAGE_VERSION}-slim
ARG GRPC_HEALTH_PROBE_VERSION=v0.4.2

ENV APP_PORT=9091
ENV MODEL_DIR=/model

ENV POETRY_HOME="/opt/poetry"
ENV VENV_PATH="/opt/pysetup/.venv"
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

VOLUME /model
LABEL DEPLOYMENT_TYPE=APP

RUN apt-get update && \
    apt-get -y install wget curl sudo

RUN wget -qO/bin/grpc_health_probe https://github.com/grpc-ecosystem/grpc-health-probe/releases/download/${GRPC_HEALTH_PROBE_VERSION}/grpc_health_probe-linux-amd64 && \
    chmod +x /bin/grpc_health_probe
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python

HEALTHCHECK --start-period=10s CMD /bin/grpc_health_probe -addr=:${APP_PORT}

WORKDIR /app

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction

COPY . /app/

RUN chmod +x /app/src/main.py
RUN sync 

RUN useradd -u 42069 app && \
    mkdir /home/app && \
    chown app /home/app && \
    chown app /app && \
    chmod +x /app/start.sh

RUN echo "app ALL=NOPASSWD: /usr/bin/apt" > /etc/sudoers
USER app

CMD ["/app/start.sh"]
