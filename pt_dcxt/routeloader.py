# -*- coding: utf-8 -*-

from functools import wraps
from collections import OrderedDict
import json
import hashlib

from flask import Blueprint, request, abort, render_template, make_response, jsonify
import markdown

from objectchecker import ObjectChecker

def get_md5(s):
    md5 = hashlib.md5()
    md5.update(str(s))

    md5_string = md5.hexdigest()
    return md5_string

def render_md(text):
    exts = [
        'markdown.extensions.extra',
    ]
    return markdown.markdown(text, extensions=exts)

def flatten_param_config(param_config, cur_key=None):
    d = OrderedDict()
    sep = '.'

    if cur_key:
        d[cur_key] = {}

        if '$' in param_config:
            d[cur_key]['$type'] = 'array'
        else:
            d[cur_key]['$type'] = 'json'

    else:
        sep     = ''
        cur_key = ''

    for k, v in param_config.items():
        if k == '$':
            child = flatten_param_config(v, '.0')
            for child_k, child_v in child.items():
                d[cur_key + child_k] = child_v

        elif k[0] == '$':
            d[cur_key][k] = v

        else:
            child = flatten_param_config(v, sep + k)
            for child_k, child_v in child.items():
                d[cur_key + child_k] = child_v

    return d

def gen_param_sample(param_config):
    flattened_param_config = flatten_param_config(param_config)

    d = OrderedDict()
    for k, v in flattened_param_config.items():
        parts = k.split('.')
        obj = d
        for i in range(len(parts)):
            step = parts[i]
            prev_step = None
            if i >= 1:
                prev_step = parts[i - 1]

            is_array = isinstance(obj, (tuple, list))

            if (isinstance(obj, (dict, OrderedDict)) and obj.get(step) is None) or (isinstance(obj, list) and step.isalnum() and len(obj) < int(step) + 1):
                _type = v.get('$type')
                if _type == 'enum':
                    if is_array:
                        auto_example = [v.get('$in')[0], v.get('$in')[-1]]
                        obj.extend(v.get('$example', auto_example))
                    else:
                        auto_example = v.get('$in')[0]
                        obj[step] = v.get('$example', auto_example)

                elif _type in ('str', 'string', 'commaArray'):
                    if is_array:
                        auto_example = [
                            v.get('$name') or '{}{}'.format(prev_step, 1),
                            v.get('$name') or '{}{}'.format(prev_step, 2)
                        ]
                        obj.extend(v.get('$example', auto_example))
                    else:
                        auto_example = step
                        if step == 'id' or step.endswith('Id'):
                            auto_example = 'X-00000000-0000-0000-0000-000000000000'

                        obj[step] = v.get('$example', auto_example)

                elif _type in ('int', 'integer', 'number'):
                    min_value = v.get('$minValue', 0)
                    max_value = v.get('$maxValue', min_value + 10)

                    if is_array:
                        auto_example = [min_value, max_value]
                        obj.extend(v.get('$example', auto_example))
                    else:
                        obj[step] = v.get('$example', min_value)

                elif _type == 'array':
                    if not v.get('$example'):
                        obj[step] = v.get('$example', [])
                    else:
                        if isinstance(v.get('$example'), (tuple, list)):
                            obj[step] = v.get('$example')
                        else:
                            obj[step] = [v.get('$example')]

                elif _type == 'boolean':
                    if is_array:
                        obj.extend([True, False])
                    else:
                        obj[step] = v.get('$example', False)

                elif _type in ('*', 'any'):
                    if is_array:
                        obj.extend([1, 1.2, 'String Value', True, False])
                    else:
                        obj[step] = v.get('$example', '<Any Value>')

                else:
                    if is_array:
                        obj.extend([OrderedDict()])
                    else:
                        obj[step] = v.get('$example', OrderedDict())

            if isinstance(obj, (dict, OrderedDict)):
                obj = obj[step]
            elif isinstance(obj, list):
                obj = obj[int(step)]

    return d

class RouteLoader(object):
    def __init__(self, middlewares=None):
        super(RouteLoader, self).__init__()

        self._ROUTES = []

        if hasattr(middlewares, '__call__'):
            self.middlewares = [middlewares]
        elif isinstance(middlewares, (tuple, list)):
            self.middlewares = middlewares
        else:
            self.middlewares = []

        self.doc_rule = '/docs'

    def route(self, flask_app_or_blueprint, config, middlewares=None, **options):
        def decorator(handler):
            if isinstance(flask_app_or_blueprint, Blueprint):
                config['prefix'] = flask_app_or_blueprint.url_prefix

            self._ROUTES.append({
                'config'     : config,
                'middlewares': middlewares,
            })

            # Options for original Flask route options
            rule     = config['url']
            endpoint = options.pop('endpoints', None)
            options['methods'] = [config['method']]

            @wraps(handler)
            def wrapped_handler(*args, **kwargs):
                # Check query
                if config.get('query'):
                    default_required = False
                    custom_directives = {
                      '$desc'      : None,
                      '$name'      : None,
                      '$type'      : None,
                      '$example'   : None,
                    }

                    checker = ObjectChecker(default_required=default_required, custom_directives=custom_directives)

                    incomming_query = request.args
                    ret = checker.check(incomming_query, config.get('query'))
                    if not ret.get('isValid'):
                        # !! Change check failure response here
                        abort(make_response(jsonify(ret), 400))

                # Check body
                if config.get('body'):
                    default_required = False
                    custom_directives = {
                      '$desc'      : None,
                      '$name'      : None,
                      '$example'   : None,
                    }

                    checker = ObjectChecker(default_required=default_required, custom_directives=custom_directives)

                    incomming_data = request.get_data(as_text=True)
                    if incomming_data:
                        try:
                            incomming_body = json.loads(incomming_data)
                        except Exception as e:
                            ret = 'Invalid JSON string'
                            abort(make_response(jsonify(ret), 400))
                        else:
                            ret = checker.check(incomming_body, config.get('body'))
                            if not ret.get('isValid'):
                                # !! Change check failure response here
                                abort(make_response(jsonify(ret), 400))

                # Run extra checkers
                if self.middlewares:
                    for checker in self.middlewares:
                        checker(config)

                # Run handler
                return handler(*args, **kwargs)

            return flask_app_or_blueprint.add_url_rule(rule, endpoint, wrapped_handler, **options)

        return decorator

    def doc_handler(self):
        routes = filter(lambda r: r.get('config', {}).get('showInDoc') is True, self._ROUTES)
        page_data = {
            'doc_rule'            : self.doc_rule,
            'routes'              : routes,
            'isinstance'          : isinstance,
            'list'                : list,
            'tuple'               : tuple,
            'json'                : json,
            'flatten_param_config': flatten_param_config,
            'gen_param_sample'    : gen_param_sample,
            'render_md'           : render_md,
            'get_md5'             : get_md5,
        }
        return render_template('api_doc.html', **page_data)

    def create_doc(self, flask_app_or_blueprint, rule=None):
        if rule is not None:
            self.doc_rule = rule

        options = {
            'methods': ['GET']
        }
        return flask_app_or_blueprint.add_url_rule(self.doc_rule, None, self.doc_handler, **options)
