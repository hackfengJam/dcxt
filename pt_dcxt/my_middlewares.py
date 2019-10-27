# -*- coding: utf-8 -*-

from flask import request, abort, make_response

def global_middlewares_1(config):
    print('IN global_middlewares_1')

    if request.args.get('abort') == 'global_middlewares_1':
        abort(make_response('Abort in global_middlewares_1', 400))

def global_middlewares_2(config):
    print('IN global_middlewares_2')

    if request.args.get('abort') == 'global_middlewares_2':
        abort(make_response('Abort in global_middlewares_2', 400))

def api_middlewares_1(config):
    print('IN api_middlewares_1')

    if request.args.get('abort') == 'api_middlewares_1':
        abort(make_response('Abort in api_middlewares_1', 400))

def api_middlewares_2(config):
    print('IN api_middlewares_2')

    if request.args.get('abort') == 'api_middlewares_2':
        abort(make_response('Abort in api_middlewares_2', 400))