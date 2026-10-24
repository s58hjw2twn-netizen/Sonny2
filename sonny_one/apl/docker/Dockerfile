# APL-001 isolated evaluation image (research only)
# Build offline only after the base image and wheels have been independently
# acquired, audited, and pinned. No network access is required at runtime.
ARG PYTHON_BASE
FROM ${PYTHON_BASE}
COPY wheels/ /opt/wheels/
COPY requirements.lock /opt/requirements.lock
RUN python -m pip install --no-index --require-hashes --find-links=/opt/wheels -r /opt/requirements.lock && \
    python -m pip check
WORKDIR /src
ENTRYPOINT []
