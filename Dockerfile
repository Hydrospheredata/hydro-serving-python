# syntax=docker/dockerfile:1
ARG PYTHON_IMAGE_VERSION=3.7
FROM python:${PYTHON_IMAGE_VERSION}-slim as base
LABEL DEPLOYMENT_TYPE="APP" maintainer="support@hydrosphere.io"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_PATH=/opt/poetry \
    VENV_PATH=/opt/pysetup/.venv \
    POETRY_VERSION=1.1.6 
ENV PATH="$POETRY_PATH/bin:$VENV_PATH/bin:$PATH"

FROM base AS build

RUN apt-get update && apt-get -y install \
    curl \
    sudo \
    wget && \
    \
    GRPC_HEALTH_PROBE_VERSION=v0.4.2 && wget -qO/bin/grpc_health_probe https://github.com/grpc-ecosystem/grpc-health-probe/releases/download/${GRPC_HEALTH_PROBE_VERSION}/grpc_health_probe-linux-amd64 && \
    chmod +x /bin/grpc_health_probe && \
    \
    curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python && \
    mv /root/.poetry $POETRY_PATH && \
    python -m venv $VENV_PATH && \
    poetry config virtualenvs.create false && \
    poetry config experimental.new-installer false && \
    pip install --upgrade pip && \
    rm -rf /var/lib/apt/lists/*

COPY poetry.lock pyproject.toml ./
RUN poetry install --no-interaction


FROM base as runtime

RUN useradd -u 42069 --create-home --shell /bin/bash app

WORKDIR /home/app

ENV APP_PORT=9091
EXPOSE ${APP_PORT}
HEALTHCHECK --start-period=10s CMD /bin/grpc_health_probe -addr=:${APP_PORT}

COPY --from=build --chown=app:app /bin/grpc_health_probe /bin/grpc_health_probe
COPY --from=build --chown=app:app $VENV_PATH $VENV_PATH

ENV MODEL_DIR=/model

VOLUME /model

COPY --chown=app:app src/ /home/app/src/
COPY --chown=app:app start.sh start.sh

RUN chmod +x /home/app/src/main.py && \
    sync && \
    chmod +x /home/app/start.sh

RUN echo "app ALL=NOPASSWD: /usr/bin/apt" > /etc/sudoers
USER app

ENTRYPOINT ["bash", "/home/app/start.sh"]
