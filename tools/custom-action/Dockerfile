FROM debian:12.6

ENV LANG=en_US.UTF-8

RUN \
  export DEBIAN_FRONTEND=noninteractive && \
  apt update -y && \
  apt install -y locales && \
  locale-gen en_US.UTF-8 && \
  apt install -y \
    build-essential \
    clang \
    chromium \
    nodejs \
    npm \
    git \
    sudo \
    libgtk-3-dev \
    libnotify-dev \
    libnss3 \
    libxss1 \
    libasound2 \
    python3-full \
    python3-pip \
    rsync && \
  chsh -s /bin/bash

SHELL ["/bin/bash", "-c"]

COPY tools/custom-action/entrypoint.sh tools/custom-action/prepare.sh tools/custom-action/dependency-versions.sh /

COPY wgsl/grammar /grammar

RUN \
  update-alternatives --install /usr/bin/cc cc /usr/bin/clang 100 && \
  update-alternatives --install /usr/bin/c++ c++ /usr/bin/clang++ 100

ENV CC=clang
ENV CXX=clang++

RUN \
  chmod +x /entrypoint.sh /prepare.sh /dependency-versions.sh && \
  source /dependency-versions.sh && \
  python3 -m pip install --break-system-packages \
    build==$PIP_BUILD_VERSION \
    tree_sitter==$PIP_TREE_SITTER_VERSION && \
  npm install -g @mermaid-js/mermaid-cli@$NPM_MERMAID_CLI_VERSION && \
  npm install -g tree-sitter-cli@$NPM_TREE_SITTER_CLI_VERSION && \
  cd /grammar && \
  npm install

ENTRYPOINT [ "/entrypoint.sh" ]
