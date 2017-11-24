FROM python:3.6.3-alpine3.6

WORKDIR app
COPY requirements.txt /app/requirements.txt

# build dependencies
RUN \
apk add --update --no-cache --virtual=build-deps \
    ca-certificates \
    g++ \
    gcc \
    git \
    linux-headers \
    make && \
# runtime dependencies
apk add --update --no-cache \
    su-exec && \
# pip packages
pip install --no-cache-dir -U \
    pip && \
pip install --no-cache-dir -r \
    requirements.txt && \
# cleanup
apk del --purge \
    build-deps && \
rm -rf \
    /tmp/*

COPY . /app/

# VOLUME /app/config
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "-u", "krbot.py"]
