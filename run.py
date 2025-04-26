#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-11-24 23:11:49

import os

# Set OPENSSL_CONF to /dev/null to avoid OpenSSL configuration issues
os.environ['OPENSSL_CONF'] = '/dev/null'

from pyspider.run import main

if __name__ == '__main__':
    main()
