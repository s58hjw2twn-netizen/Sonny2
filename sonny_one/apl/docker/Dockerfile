# APL-001 isolated evaluation image (research only)
# Build offline only after the base image and wheels have been independently
# acquired, audited, and pinned. No network access is required at runtime.
ARG PYTHON_BASE
FROM ${PYTHON_BASE}
ARG PYTEST_WHEEL
COPY wheels/ /opt/wheels/
RUN python -m pip install --no-index --find-links=/opt/wheels pytest && \
    python -m pip check
WORKDIR /src
ENTRYPOINT []
