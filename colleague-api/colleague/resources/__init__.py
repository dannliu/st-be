# -*- coding:utf-8 -*-

def compose_response(result=None, message=None):
    resp = {
        'status': 200,
    }
    if result:
        resp['result'] = result
    if message:
        resp['message'] = message
    return resp
