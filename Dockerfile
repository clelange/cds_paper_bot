FROM alpine:3.7

ENV ALPINE_VERSION=3.7
ENV MAGICK_HOME=/usr

# Install needed packages. Notes:
#   * musl: standard C library
#   * linux-headers: commonly needed, and an unusual package name from Alpine.
#   * bash: so we can access /bin/bash
#   * python: the binaries themselves
#   * python-dev: are used for gevent e.g.
#   * remaining libraries are for image manipulation
#   * freeimage: taken from test repository
ENV PACKAGES="\
  zlib \
  zlib-dev \
  musl \
  musl-dev \
  libgcc \
  libstdc++ \
  linux-headers \
  python3 \
  python3-dev \
  bash \
  imagemagick6 \
  imagemagick6-dev \
  py3-pillow \
  gcc \
  freeimage \
  libpng \
  libjpeg \
  "

COPY requirements.txt /tmp/requirements.txt

RUN echo \
  # replacing default repositories with edge ones
  && echo "http://dl-cdn.alpinelinux.org/alpine/v$ALPINE_VERSION/community" >> /etc/apk/repositories \
  && echo "http://dl-cdn.alpinelinux.org/alpine/v$ALPINE_VERSION/main" >> /etc/apk/repositories \
  && echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories \
  # Add the packages, with a CDN-breakage fallback if needed
  && apk add --no-cache $PACKAGES || \
  (sed -i -e 's/dl-cdn/dl-4/g' /etc/apk/repositories && apk add --no-cache $PACKAGES) \
  # turn back the clock -- so hacky!
  && echo "http://dl-cdn.alpinelinux.org/alpine/v$ALPINE_VERSION/main/" > /etc/apk/repositories \
  # install python and pip
  && python3 -m ensurepip \
  && rm -r /usr/lib/python*/ensurepip \
  && pip3 install --upgrade pip setuptools \
  # make some useful symlinks that are expected to exist
  && if [[ ! -e /usr/bin/python ]];        then ln -sf /usr/bin/python3 /usr/bin/python; fi \
  && if [[ ! -e /usr/bin/python-config ]]; then ln -sf /usr/bin/python3-config /usr/bin/python-config; fi \
  && if [[ ! -e /usr/bin/pip ]]; then ln -sf /usr/bin/pip3 /usr/bin/pip; fi \
  # install python requirements
  && pip install --no-cache-dir -r /tmp/requirements.txt

CMD = ["python"]