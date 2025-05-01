#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2023-05-01 09:15:00

import time
import json
import redis
import logging
import itertools

from pyspider.libs import utils
from pyspider.database.base.resultdb import ResultDB as BaseResultDB


class ResultDB(BaseResultDB):
    __prefix__ = 'resultdb_'

    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.StrictRedis(host=host, port=port, db=db)
        try:
            self.redis.scan(count=1)
            self.scan_available = True
        except Exception as e:
            logging.debug("redis_scan disabled: %r", e)
            self.scan_available = False
        
        self.projects = set()
        self._list_project()

    def _gen_key(self, project, taskid):
        return "%s%s_%s" % (self.__prefix__, project, taskid)

    def _gen_project_key(self, project):
        return "%s%s" % (self.__prefix__, project)

    def _list_project(self):
        if self.scan_available:
            scan_method = self.redis.scan_iter
        else:
            scan_method = self.redis.keys
            
        self.projects = set()
        for key in scan_method("%s*" % self.__prefix__):
            key = utils.text(key)
            if '_' not in key:
                project = key[len(self.__prefix__):]
                self.projects.add(project)

    def _parse(self, data):
        # Python 3.10+ compatibility
        result = {}
        for key, value in data.items():
            if isinstance(value, bytes):
                value = utils.text(value)
            result[utils.text(key)] = value
        data = result

        if 'result' in data:
            data['result'] = json.loads(data['result'])
        if 'updatetime' in data:
            data['updatetime'] = float(data['updatetime'] or 0)
        return data

    def _stringify(self, data):
        if 'result' in data:
            data['result'] = json.dumps(data['result'])
        return data

    def save(self, project, taskid, url, result):
        obj = {
            'taskid': taskid,
            'url': url,
            'result': result,
            'updatetime': time.time(),
        }
        
        # Ensure project key exists
        if project not in self.projects:
            self.redis.sadd(self.__prefix__ + 'projects', project)
            self.projects.add(project)
            
        # Save result
        self.redis.hmset(self._gen_key(project, taskid), self._stringify(obj))
        self.redis.sadd(self._gen_project_key(project), taskid)
        return True

    def select(self, project, fields=None, offset=0, limit=None):
        if project not in self.projects:
            return
            
        if self.scan_available:
            scan_method = self.redis.sscan_iter
        else:
            scan_method = self.redis.smembers
            
        count = 0
        for taskid in scan_method(self._gen_project_key(project)):
            taskid = utils.text(taskid)
            if offset and count < offset:
                count += 1
                continue
                
            if fields:
                obj = self.redis.hmget(self._gen_key(project, taskid), fields)
                if all(x is None for x in obj):
                    continue
                obj = dict(zip(fields, obj))
            else:
                obj = self.redis.hgetall(self._gen_key(project, taskid))
                
            if not obj:
                continue
                
            yield self._parse(obj)
            
            count += 1
            if limit and count >= offset + limit:
                break

    def count(self, project):
        if project not in self.projects:
            return 0
        return self.redis.scard(self._gen_project_key(project))

    def get(self, project, taskid, fields=None):
        if project not in self.projects:
            return None
            
        if fields:
            obj = self.redis.hmget(self._gen_key(project, taskid), fields)
            if all(x is None for x in obj):
                return None
            obj = dict(zip(fields, obj))
        else:
            obj = self.redis.hgetall(self._gen_key(project, taskid))
            
        if not obj:
            return None
        return self._parse(obj)

    def drop(self, project):
        if project not in self.projects:
            return
            
        # Get all keys for this project
        if self.scan_available:
            scan_method = self.redis.scan_iter
        else:
            scan_method = self.redis.keys
            
        keys = list(scan_method("%s%s_*" % (self.__prefix__, project)))
        if keys:
            self.redis.delete(*keys)
            
        # Remove project from projects set
        self.redis.delete(self._gen_project_key(project))
        self.redis.srem(self.__prefix__ + 'projects', project)
        self.projects.remove(project)
        return True
