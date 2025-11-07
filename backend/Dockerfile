FROM cgr.dev/chainguard/wolfi-base:latest
RUN apk add curl build-base posix-libc-utils trufflehog git gcc

WORKDIR /home/root

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

RUN mkdir -p .cache/uv
RUN curl -LsSf https://astral.sh/uv/install.sh > install.sh && sh install.sh && rm install.sh
ENV PATH="/home/root/.cargo/bin:/home/root/app/.venv/bin:/root/.local/bin:$PATH"

RUN uv python install 3.12 
RUN uv venv
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    CC=gcc uv sync --frozen --no-install-project --no-dev

COPY . .

CMD ["uv", "run", "gunicorn", "-k", "uvicorn.workers.UvicornWorker", "chitragupta.asgi:application", "--workers", "4", "--bind", "0.0.0.0:8000"]