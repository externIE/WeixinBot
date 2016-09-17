 #!/usr/bin/env python
# coding: utf-8
import json
import os
def _decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value
    return rv
def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv

def loadConfig():
    fileName = 'config.json'
    dirName = os.path.join(os.getcwd(), 'config')
    fn = os.path.join(dirName, fileName)
    with open(fn, 'r') as f:
        config = json.loads(f, object_hook=_decode_dict)
        print json.dumps(config, indent=4)
        print config
        print '\n[*] 成功加载配置文件...'

    if config['DEBUG']:
        print config['DEBUG']
    if config['autoReplyMode']:
        print config['autoReplyMode']
    if config['user_agent']:
        print config['user_agent']
    if config['interactive']:
        print config['interactive']
    if config['autoOpen']:
        print config['autoOpen']
    if config['NoReplyGroupList']:
        print config['NoReplyGroupList']
        print config['NoReplyGroupList'][0]


if __name__ == '__main__':
    loadConfig()