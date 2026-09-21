FROM python:3.11-slim

WORKDIR /workspace

# Install pytest and essential testing dependencies
RUN pip install --no-cache-dir pytest

# Create unprivileged runner user
RUN useradd -m -u 1000 agentforge && chown -R agentforge:agentforge /workspace

USER agentforge

CMD ["pytest", "-v", "--tb=short"]
