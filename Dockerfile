FROM python:3.13-slim-bookworm

ENV MAGICK_HOME=/usr

# Install needed packages. Notes:
ENV PACKAGES="\
  build-essential \
  bash \
  imagemagick \
  imagemagick-common \
  libmagickwand-dev \
  libpng-dev \
  libjpeg-dev \
  libfreeimage-dev \
  ghostscript \
  git \
  openssh-client \
  ffmpeg \
  fonts-dejavu-core \
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
  # Update the bundled Python toolchain
  && python -m pip install --upgrade pip setuptools \
  # install python requirements
  && pip install --no-cache-dir --ignore-installed -r /tmp/requirements.txt

CMD ["python"]
