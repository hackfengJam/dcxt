# -*- coding: utf-8 -*-

import os
import json

try:
    # Use oyaml to keep the key orders
    import oyaml as yaml
except ImportError:
    import yaml

from flask import Flask, Blueprint, request, render_template, jsonify

from routeloader import RouteLoader
from my_middlewares import global_middlewares_1, global_middlewares_2, api_middlewares_1, api_middlewares_2
from my_decorators import api_decorator_1, api_decorator_2



##### Init RouteLoader #####

# Load API config file
ROUTE = None
basedir = os.path.abspath(os.path.dirname(__file__))
with open(basedir + '/route.yaml') as _f:
    ROUTE = yaml.load(_f.read())



##### Use RouteLoader on Flask app object #####
# Init RouteLoader
global_middlewares = [
    global_middlewares_1,
    global_middlewares_2,
]
route_loader = RouteLoader(middlewares=global_middlewares)

# Flask app object
app = Flask(__name__)

@route_loader.route(app, ROUTE['app']['index'])
def index():
    return render_template('index.html')

@route_loader.route(app, ROUTE['app']['doPost'], middlewares=[api_middlewares_1, api_middlewares_2])
@api_decorator_1
@api_decorator_2
def do_post():
    ret = request.get_data(as_text=True)

    return ret



##### Use RouteLoader on Flask blueprint object #####

# Flask blueprint object
#!!! Notice: Set `url_prefix` here (before `@route_loader.route`) !!!
my_module_bp = Blueprint('my_module', __name__, url_prefix='/my_module')

@route_loader.route(my_module_bp, ROUTE['myModule']['index'])
def my_module_index():
    return render_template('my_module_index.html')

@route_loader.route(my_module_bp, ROUTE['myModule']['doPost'])
def my_module_do_post(**kwargs):
    body = json.loads(request.get_data(as_text=True))
    print body
    return jsonify({"param": kwargs, "body": body})

@route_loader.route(my_module_bp, ROUTE['myModule']['doPostWithOutBody'])
def my_module_do_post_without_body(**kwargs):
    return jsonify({"param": kwargs})

# Register blueprint
app.register_blueprint(my_module_bp)



##### API Documents #####
route_loader.create_doc(app, '/doc')



##### Other options #####
app.config['TEMPLATES_AUTO_RELOAD'] = True
