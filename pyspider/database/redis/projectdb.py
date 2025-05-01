#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2023-05-01 09:10:00

import time
import json
import redis
import logging

from pyspider.libs import utils
from pyspider.database.base.projectdb import ProjectDB as BaseProjectDB


class ProjectDB(BaseProjectDB):
    __prefix__ = 'projectdb_'

    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.StrictRedis(host=host, port=port, db=db)
        try:
            self.redis.scan(count=1)
            self.scan_available = True
        except Exception as e:
            logging.debug("redis_scan disabled: %r", e)
            self.scan_available = False

    def _gen_key(self, name):
        return "%s%s" % (self.__prefix__, name)

    def _parse(self, data):
        # Python 3.10+ compatibility
        result = {}
        for key, value in data.items():
            if isinstance(value, bytes):
                value = utils.text(value)
            result[utils.text(key)] = value
        data = result

        if 'rate' in data:
            data['rate'] = float(data['rate'])
        if 'burst' in data:
            data['burst'] = float(data['burst'])
        if 'updatetime' in data:
            data['updatetime'] = float(data['updatetime'] or 0)
        return data

    def _stringify(self, data):
        return data

    def insert(self, name, obj={}):
        obj = dict(obj)
        obj['name'] = name
        obj['updatetime'] = time.time()
        
        self.redis.hmset(self._gen_key(name), self._stringify(obj))
        self.redis.sadd(self.__prefix__ + 'projects', name)
        return True

    def update(self, name, obj={}, **kwargs):
        obj = dict(obj)
        obj.update(kwargs)
        obj['updatetime'] = time.time()
        
        self.redis.hmset(self._gen_key(name), self._stringify(obj))
        return True

    def get_all(self, fields=None):
        for name in self.redis.smembers(self.__prefix__ + 'projects'):
            name = utils.text(name)
            if fields:
                obj = self.redis.hmget(self._gen_key(name), fields)
                if all(x is None for x in obj):
                    continue
                obj = dict(zip(fields, obj))
            else:
                obj = self.redis.hgetall(self._gen_key(name))
            
            if not obj:
                continue
            obj = self._parse(obj)
            yield obj

    def get(self, name, fields=None):
        if fields:
            obj = self.redis.hmget(self._gen_key(name), fields)
            if all(x is None for x in obj):
                return None
            obj = dict(zip(fields, obj))
        else:
            obj = self.redis.hgetall(self._gen_key(name))
        
        if not obj:
            return None
        return self._parse(obj)

    def check_update(self, timestamp, fields=None):
        for name in self.redis.smembers(self.__prefix__ + 'projects'):
            name = utils.text(name)
            updatetime = self.redis.hget(self._gen_key(name), 'updatetime')
            if updatetime and float(updatetime) > timestamp:
                if fields:
                    obj = self.redis.hmget(self._gen_key(name), fields)
                    if all(x is None for x in obj):
                        continue
                    obj = dict(zip(fields, obj))
                else:
                    obj = self.redis.hgetall(self._gen_key(name))
                yield self._parse(obj)

    def drop(self, name):
        self.redis.delete(self._gen_key(name))
        self.redis.srem(self.__prefix__ + 'projects', name)
        return True
