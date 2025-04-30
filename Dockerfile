FROM python:3.13
MAINTAINER binux <roy@binux.me>

# PhantomJS has been removed as it is deprecated
# Fix Error: libssl_conf.so: cannot open shared object file: No such file or directory
ENV OPENSSL_CONF=/etc/ssl/

# install nodejs
ENV NODEJS_VERSION=20.11.1 \
    PATH=$PATH:/opt/node/bin
WORKDIR "/opt/node"
RUN apt-get -qq update && apt-get -qq install -y curl ca-certificates libx11-xcb1 libxtst6 libnss3 libasound2 libatk-bridge2.0-0 libgtk-3-0 --no-install-recommends && \
    curl -sL https://nodejs.org/dist/v${NODEJS_VERSION}/node-v${NODEJS_VERSION}-linux-x64.tar.gz | tar xz --strip-components=1 && \
    rm -rf /var/lib/apt/lists/*
RUN npm install puppeteer express

# install requirements
COPY requirements.txt /opt/pyspider/requirements.txt
RUN pip install -r /opt/pyspider/requirements.txt

# add all repo
ADD ./ /opt/pyspider

# run test
WORKDIR /opt/pyspider
RUN pip install -e .[all]

# Create a symbolic link to node_modules
RUN ln -s /opt/node/node_modules ./node_modules

#VOLUME ["/opt/pyspider"]
ENTRYPOINT ["pyspider"]

EXPOSE 5000 23333 24444 22222
