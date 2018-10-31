FROM mhart/alpine-node:10

# Create and set the default working directory
WORKDIR /usr/src

# Copy package.json, lock file, and webidl for the build
COPY package.json yarn.lock validate-idl.js ./

# Install dependencies
RUN yarn

COPY design/sketch.webidl .

RUN mkdir /public

# Validate webidl
RUN node validate-idl.js sketch.webidl > /public/index.txt
