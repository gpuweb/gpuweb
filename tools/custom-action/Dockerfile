FROM ubuntu:23.10

ENV LANG=en_US.UTF-8

RUN \
  export DEBIAN_FRONTEND=noninteractive && \
  apt update -y && \
  apt install -y locales && \
  locale-gen en_US.UTF-8 && \
  sysctl -w kernel.unprivileged_userns_clone=1 && \
  apt install -y \
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

COPY entrypoint.sh prepare.sh dependency-versions.sh /

RUN \
  chmod +x /entrypoint.sh /prepare.sh /dependency-versions.sh && \
  source /dependency-versions.sh && \
  python3 -m pip install --break-system-packages \
    tree_sitter==$PIP_TREE_SITTER_VERSION && \
  npm install -g @mermaid-js/mermaid-cli@$NPM_MERMAID_CLI_VERSION && \
  npm install -g tree-sitter-cli@$NPM_TREE_SITTER_CLI_VERSION && \
  mkdir /grammar && \
  echo "{" > /grammar/package.json && \
  echo "  \"name\": \"tree-sitter-wgsl\"," >> /grammar/package.json && \
  echo "  \"dependencies\": {" >> /grammar/package.json && \
  echo "    \"nan\": \"$NPM_NAN_VERSION\"" >> /grammar/package.json && \
  echo "  }," >> /grammar/package.json && \
  echo "  \"devDependencies\": {" >> /grammar/package.json && \
  echo "    \"tree-sitter-cli\": \"$NPM_TREE_SITTER_CLI_VERSION\"" >> /grammar/package.json && \
  echo "  }," >> /grammar/package.json && \
  echo "  \"main\": \"bindings/node\"" >> /grammar/package.json && \
  echo "}" >> /grammar/package.json && \
  cd /grammar && \
  npm install

ENTRYPOINT [ "/entrypoint.sh" ]
