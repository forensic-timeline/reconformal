FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY README.md .
COPY LICENSE .
COPY reconformal/ reconformal/

RUN pip install --no-cache-dir .

# Force non-interactive matplotlib backend (no display needed inside container)
ENV MPLBACKEND=Agg

ENTRYPOINT ["reconformal"]
CMD ["--help"]
