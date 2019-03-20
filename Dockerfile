FROM ubuntu:18.04

ENV MAGICK_HOME=/usr

# Install needed packages. Notes:
ENV PACKAGES="\
  build-essential \
  python3 \
  python3-dev \
  python3-pip \
  bash \
  imagemagick-common \
  libmagickwand-dev \
  libpng-dev \
  libjpeg-dev \
  libfreeimage-dev \
  ghostscript \
  git \
  openssh-client \
  "

COPY requirements.txt /tmp/requirements.txt

RUN \
  apt-get update \
  && apt-get install --no-install-recommends --no-install-suggests -y ${PACKAGES} \
  && rm -rf /var/lib/apt/lists/* \
  # fix ImageMagick permissions
  && sed -i '/MVG/d' /etc/ImageMagick-6/policy.xml \
  && sed -i '/PDF/{s/none/read|write/g}' /etc/ImageMagick-6/policy.xml \
  && sed -i '/PDF/ a <policy domain="coder" rights="read|write" pattern="LABEL" />' /etc/ImageMagick-6/policy.xml \
  # install python and pip
  && pip3 install --upgrade pip setuptools \
  # make some useful symlinks that are expected to exist
  && /bin/bash -c "if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi" \
  && /bin/bash -c "if [[ ! -e /usr/bin/python-config ]]; then ln -sf /usr/bin/python3-config /usr/bin/python-config; fi" \
  && /bin/bash -c "if [[ ! -e /usr/bin/pip ]]; then ln -sf /usr/bin/pip3 /usr/bin/pip; fi" \
  # install python requirements
  && pip install --no-cache-dir --ignore-installed -r /tmp/requirements.txt

CMD = ["python"]