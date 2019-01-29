import re
from flask import Flask
from flask import render_template
from flask import request
from flask_bootstrap import Bootstrap

from lib.marc_validator import MarcValidator
from lib.settings import PREP_CONFIGS, REPOSITORIES

def build_repo_tag_name_map():
    tag_name_map = {}
    for config in REPOSITORIES['configs']:
        tag = config['tag']
        name = config['name']
        tag_name_map[tag] = name

    return tag_name_map

REPO_TAG_NAME_MAP = build_repo_tag_name_map()

def prep_config_name(prep_config_tag):

    config = PREP_CONFIGS[prep_config_tag]
    repo_tag = config['repository']['tag']
    prep_tag = config['repository_prep']['tag']
    name = "%s - %s (%s)" % (prep_tag.upper(), REPO_TAG_NAME_MAP[repo_tag], prep_config_tag)

    return name

def build_marc_configs():
    keys = [x for x in PREP_CONFIGS if re.match('(pih|mmw)', PREP_CONFIGS[x]['repository_prep']['tag'])]
    key_names = []
    for key in keys:
        name = prep_config_name(key)
        key_names.append([key, name])
    clamp = lambda x,y: cmp(x[1], y[1])
    key_names.sort(clamp)

    return key_names

MARC_CONFIGS = build_marc_configs()

def find_prep_config_name(prep_config_tag):
    for config in MARC_CONFIGS:
        if config[0] == prep_config_tag:
            return config[1]

def param_value(form, param):
    if form[param] == '':
        return None
    else:
        return form[param]

def required_xpaths(prep_config_tag):
    config = PREP_CONFIGS[prep_config_tag]
    params = config['repository_prep'].get('params', None)
    if params is None:
        return []

    xpaths = params.get('required_xpaths', None)
    if xpaths is None:
        return []

    return xpaths

def create_app():
  app = Flask(__name__)
  Bootstrap(app)

  return app

app = create_app()

@app.route('/')
def hello_world():
    return render_template('index.html', marc_configs=MARC_CONFIGS)

@app.route('/validate', methods=['POST',])
def validate():
    xml = request.files['xml_file']
    prep_config_tag = param_value(request.form, 'prep_config')
    holdings_id = param_value(request.form, 'holdings_id')
    xpaths = required_xpaths(prep_config_tag)
    validator = MarcValidator(xml, xpaths, holdings_id)
    validator.validate()
    kwargs = {
        'validator': validator,
        'holdings_id': holdings_id,
        'prep_config_tag':  prep_config_tag,
        'prep_config_name': find_prep_config_name(prep_config_tag),
        'required_xpaths': xpaths,
        'file_name': request.files['xml_file'].filename
    }
    return render_template('results.html', **kwargs)