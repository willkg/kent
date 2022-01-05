FROM python:3.10.1-alpine3.15

WORKDIR /app/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# NOTE(willkg): This installs Kent from main tip. If you're using Kent for
# realzies, you probably don't want to do this because Kent could change and
# break all your stuff. Naughty Kent!
RUN pip install -U 'pip>=8' && \
    pip install --no-cache-dir 'https://github.com/willkg/kent/archive/refs/heads/main.zip'

USER guest

ENTRYPOINT ["/usr/local/bin/kent-server"]
CMD ["run"]
