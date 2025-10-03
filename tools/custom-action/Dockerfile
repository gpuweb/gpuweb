FROM ubuntu:25.04

ENV LANG=en_US.UTF-8
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/root/.cache/ms-playwright/chromium_headless_shell-1179/chrome-linux/headless_shell

RUN \
  export DEBIAN_FRONTEND=noninteractive && \
  apt update -y && \
  apt install -y locales && \
  locale-gen en_US.UTF-8 && \
  apt install -y \
    build-essential \
    clang \
    emscripten \
    nodejs \
    npm \
    git \
    sudo \
    libgtk-3-dev \
    libnotify-dev \
    libnss3 \
    libxss1 \
    libasound2t64 \
    python3-full \
    python3-pip \
    python3-setuptools \
    rsync \
    util-linux && \
  chsh -s /bin/bash

SHELL ["/bin/bash", "-c"]

COPY tools/custom-action/entrypoint.sh tools/custom-action/prepare.sh tools/custom-action/dependency-versions.sh /

RUN \
  update-alternatives --install /usr/bin/cc cc /usr/bin/clang 100 && \
  update-alternatives --install /usr/bin/c++ c++ /usr/bin/clang++ 100

ENV CC=clang
ENV CXX=clang++

RUN \
  chmod +x /entrypoint.sh /prepare.sh /dependency-versions.sh && \
  source /dependency-versions.sh && \
  npm install -g playwright@$NPM_PLAYWRIGHT_VERSION && \
  playwright install chromium --with-deps --only-shell && \
  python3 -m pip install --break-system-packages \
    build==$PIP_BUILD_VERSION \
    tree_sitter==$PIP_TREE_SITTER_VERSION && \
  npm install -g @mermaid-js/mermaid-cli@$NPM_MERMAID_CLI_VERSION && \
  npm install -g tree-sitter-cli@$NPM_TREE_SITTER_CLI_VERSION

COPY wgsl /wgsl

RUN \
  source /dependency-versions.sh && \
  cd /wgsl && \
  script -q -c "make grammar/grammar.js SHELL=/bin/bash" /dev/null && \
  cd /wgsl/grammar && \
  script -q -c "tree-sitter init --update" /dev/null && \
  tree-sitter generate && \
  python3 -m pip install -e . --break-system-packages

ENTRYPOINT [ "/entrypoint.sh" ]
