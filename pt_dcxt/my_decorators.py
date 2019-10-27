# -*- coding: utf-8 -*-

from functools import wraps

from flask import request

def api_decorator_1(handler):
    @wraps(handler)
    def wrapped_api_decorator_1(*args, **kwargs):
        print('IN api_decorator_1')

        return handler(*args, **kwargs)

    return wrapped_api_decorator_1

def api_decorator_2(handler):
    @wraps(handler)
    def wrapped_api_decorator_2(*args, **kwargs):
        print('IN api_decorator_2')

        return handler(*args, **kwargs)

    return wrapped_api_decorator_2