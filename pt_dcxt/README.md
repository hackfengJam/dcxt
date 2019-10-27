# RouteLoader (for Flask)

RouteLoader is an API managing tool for Flask, including：
1. API descriptions managing
2. Checking incoming request according to API descriptions
3. Generating API Documents according to API descriptions



## Quick Example

*Notice: For a full example, please see [demo.py](demo.py) and other related files.*

```python
# -*- coding: utf-8 -*-
try:
    # Use oyaml to keep the key orders
    import oyaml as yaml
except ImportError:
    import yaml

from flask import Flask, Blueprint, request, render_template, jsonify
from routeloader import RouteLoader

##### Init RouteLoader #####

# Load API config file
ROUTE = yaml.load("""---
app:
  index:
    showInDoc: true
    name     : Flask app index
    method   : get
    url      : "/"
    response : html
  doPost:
    showInDoc: true
    name     : Flask app POST example
    method   : post
    url      : "/do_post"
    response : json
    body:
      data:
        id:
          "$desc"      : ID
          "$isRequired": true
          "$type"      : int
          "$example"   : 1
""")

##### Use RouteLoader on Flask app object #####
# Init RouteLoader
route_loader = RouteLoader()

# Flask app object
app = Flask(__name__)

@route_loader.route(app, ROUTE['app']['index'])
def index():
    return render_template('index.html')

@route_loader.route(app, ROUTE['app']['doPost'])
def do_post():
    ret = request.get_data(as_text=True)

    return ret

##### API Documents #####
route_loader.create_doc(app, '/doc')
```



## File list

|                               File                               |   Type   |                            Description                             |
|------------------------------------------------------------------|----------|--------------------------------------------------------------------|
| [routeloader.py](routeloader.py)                                 | Core     | RouteLoader core code (Routeloader)                                |
| [objectchecker.py](objectchecker.py)                             | Core     | RouteLoader core code (JSON checker)                               |
| [templates/api_docs.html](templates/api_docs.html)               | Core     | RouteLoader core code (API Document template                       |
| [static/\*](static)                                              | Resource | API Document css/js/font Resource                                  |
| [route.yaml](route.yaml)                                         | Example  | Route file in YAML format                                          |
| [demo.py](demo.py)                                               | Example  | Flask project example code                                         |
| [my_middlewares.py](my_middlewares.py)                           | Example  | Example middlewares for Flask                                      |
| [my_decorators.py](my_decorators.py)                             | Example  | Example decorators for Flask                                       |
| [templates/\_base.html](templates/_base.html)                    | Example  | Flask project example template (Base template)                     |
| [templates/\_macros.html](templates/_macros.html)                | Example  | Flask project example template (Macros)                            |
| [templates/index.html](templates/index.html)                     | Example  | Flask project example template (Flask app index template)          |
| [templates/my_module_index.html](templates/my_module_index.html) | Example  | Flask project example template (MyModule blueprint index template) |



## Variable `USE_CSS_JS_FONT_RESOURCE_FROM_CDN` in `api_doc.html`

|  Value  |                  Description                   |
|---------|------------------------------------------------|
| `True`  | *Default*: Load css/js/font resources fron CDN |
| `False` | Load css/js/font resources from static folder  |

*Notice: You can change the URL of the resources if you have a different static file path.*