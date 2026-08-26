# The sealed, disposable box the generated script runs in.
#
# It exists so that a resource kill produces a real exit code (137) that a
# process outside can read. Nothing in here observes anything.
FROM python:3.12-slim

COPY app/sandbox/runner.py /app/runner.py
COPY data /data

# No network, no writable filesystem, and a memory ceiling are applied by the
# host at `docker run` time, not baked in here — the host sets the terms.
ENTRYPOINT ["python", "/app/runner.py"]
