FROM python:3.10.8-alpine3.16

WORKDIR /app/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY . .
RUN pip install -U 'pip>=' .

USER guest

ENTRYPOINT ["/usr/local/bin/kent-server"]
CMD ["run"]
