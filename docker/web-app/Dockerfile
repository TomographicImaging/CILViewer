ARG BASE_IMAGE=ubuntu:20.04
FROM ${BASE_IMAGE} as base

LABEL \
  author.name="Edoardo Pasca, Laura Murgatroyd , Samuel Jones" \
  author.email=edoardo.pasca@stfc.ac.uk \
  maintainer.email=edoardo.pasca@stfc.ac.uk \
  maintainer.url=https://www.ccpi.ac.uk/  \
  source.url=https://github.com/vais-ral/CILViewer  \
  licence="Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)"  \
  description="CILViewer Ubuntu"

ENV LANG en_GB.UTF-8
ENV LANGUAGE en_GB:en

ARG USER="abc"
ARG GROUP="users"
ARG HOME="/home/${USER}"
WORKDIR ${HOME}

USER root
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install curl git -y && \
    # Add VTK dependencies and xvfb for running displays in a container
    apt-get install libgl1 libxrender1 libgl1-mesa-dev xvfb -y

USER ${NB_USER}:${NB_GROUP}

COPY environment.yml .
COPY install-mambaforge-and-env.sh .
RUN bash install-mambaforge-and-env.sh
RUN rm install-mambaforge-and-env.sh
RUN rm environment.yml

COPY clone-and-install.sh .
RUN bash clone-and-install.sh
RUN rm clone-and-install.sh

COPY create-data-folder.sh .
RUN bash create-data-folder.sh
RUN rm create-data-folder.sh

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

