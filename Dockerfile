FROM ubuntu:24.04
WORKDIR /opt/re-toolbox
COPY requirements.txt .
COPY scripts/setup scripts/env scripts/
RUN ./scripts/setup --install
COPY scripts/ scripts/
COPY .codex/ .codex/
COPY AGENTS.md README.md ./
ENV PATH="/opt/re-toolbox/.venv/bin:/opt/re-toolbox/.local/cargo/bin:${PATH}"
CMD ["bash", "--rcfile", "scripts/env"]
