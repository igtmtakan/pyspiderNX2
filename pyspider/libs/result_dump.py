#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-03-27 20:12:11


import csv
import json
import itertools
import re
from io import StringIO



def result_formater(results):
    common_fields = None
    for result in results:
        result.setdefault('result', None)
        if isinstance(result['result'], dict):
            if common_fields is None:
                common_fields = set(result['result'].keys())
            else:
                common_fields &= set(result['result'].keys())
        else:
            common_fields = set()
    for result in results:
        result['result_formated'] = {}
        if not common_fields:
            result['others'] = result['result']
        elif not isinstance(result['result'], dict):
            result['others'] = result['result']
        else:
            result_formated = {}
            others = {}
            for key, value in result['result'].items():
                if key in common_fields:
                    result_formated[key] = value
                else:
                    others[key] = value
            result['result_formated'] = result_formated
            result['others'] = others
    return common_fields or set(), results


def dump_as_json(results, valid=False):
    first = True
    if valid:
        yield '['

    for result in results:
        if valid:
            if first:
                first = False
            else:
                yield ', '

        yield json.dumps(result, ensure_ascii=False) + '\n'

    if valid:
        yield ']'


def dump_as_txt(results):
    for result in results:
        yield (
            result.get('url', None) + '\t' +
            json.dumps(result.get('result', None), ensure_ascii=False) + '\n'
        )


def dump_as_csv(results):
    def toString(obj):
        if isinstance(obj, bytes):
            return obj.decode('utf8')
        elif isinstance(obj, str):
            return obj
        else:
            return json.dumps(obj, ensure_ascii=False)

    # Python 3.10+ only needs StringIO
    stringio = StringIO()
    csv_writer = csv.writer(stringio)

    it = iter(results)
    first_30 = []
    for result in it:
        first_30.append(result)
        if len(first_30) >= 30:
            break
    common_fields, _ = result_formater(first_30)
    common_fields_l = sorted(common_fields)

    csv_writer.writerow([toString('url')]
                        + [toString(x) for x in common_fields_l]
                        + [toString('...')])
    for result in itertools.chain(first_30, it):
        result['result_formated'] = {}
        if not common_fields:
            result['others'] = result['result']
        elif not isinstance(result['result'], dict):
            result['others'] = result['result']
        else:
            result_formated = {}
            others = {}
            for key, value in result['result'].items():
                if key in common_fields:
                    result_formated[key] = value
                else:
                    others[key] = value
            result['result_formated'] = result_formated
            result['others'] = others
        csv_writer.writerow(
            [toString(result['url'])]
            + [toString(result['result_formated'].get(k, '')) for k in common_fields_l]
            + [toString(result['others'])]
        )
        yield stringio.getvalue()
        stringio.truncate(0)
        stringio.seek(0)


def dump_as_xml(results):
    """
    Dump results as XML format
    """
    # XML header
    yield '<?xml version="1.0" encoding="UTF-8"?>\n'
    yield '<results>\n'
    
    for result in results:
        yield '  <result>\n'
        
        # Add URL
        url = result.get('url', '')
        yield f'    <url>{escape_xml(url)}</url>\n'
        
        # Add taskid
        taskid = result.get('taskid', '')
        yield f'    <taskid>{escape_xml(taskid)}</taskid>\n'
        
        # Add updatetime
        updatetime = result.get('updatetime', '')
        yield f'    <updatetime>{updatetime}</updatetime>\n'
        
        # Add result data
        result_data = result.get('result', {})
        yield '    <data>\n'
        
        if isinstance(result_data, dict):
            for key, value in sorted(result_data.items()):
                # XMLタグ名に使用できない文字を処理
                safe_key = make_safe_xml_tag(key)
                yield f'      <{safe_key}>{escape_xml_value(value)}</{safe_key}>\n'
        else:
            # If result is not a dict, wrap it in a value tag
            yield f'      <value>{escape_xml_value(result_data)}</value>\n'
            
        yield '    </data>\n'
        yield '  </result>\n'
    
    # XML footer
    yield '</results>\n'


def escape_xml(text):
    """
    Escape special characters for XML
    """
    if not isinstance(text, str):
        text = str(text)
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')


def escape_xml_value(value):
    """
    Convert value to string and escape for XML
    """
    if isinstance(value, (dict, list, tuple)):
        return escape_xml(json.dumps(value, ensure_ascii=False))
    elif value is None:
        return ''
    else:
        return escape_xml(value)


def make_safe_xml_tag(tag):
    """
    Make a string safe to use as an XML tag name
    """
    # XMLタグ名の最初の文字は文字またはアンダースコアでなければならない
    if not tag or not re.match(r'^[a-zA-Z_]', str(tag)):
        tag = 'field_' + str(tag)
    
    # XMLタグ名に使用できない文字を置き換える
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', str(tag))
