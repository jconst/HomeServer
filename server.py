#!/usr/bin/env python
import json
import re
import requests
import shelve
import time
from beautifulhue.api import Bridge
from datetime import datetime
from flask import Flask, Response, request, make_response

app = Flask(__name__)
app.config['DEBUG'] = True

### SETUP: ###

def setup():
  global bridge
  bridge = create_bridge()

def create_bridge():
  bridge_addr = '192.168.0.110'
  bridge = Bridge(device={'ip':bridge_addr}, 
                  user={'name':'2bb6465d7c479351631cd18e4daad16f'})
  return bridge

def set_lr_tree_brightness(brightness):
  url = 'http://192.168.0.120/'
  requests.post(url, data=str(brightness))

### ROUTES: ###

@app.route('/')
def list_scenes():
  return make_response(str(load_db()), 200)

@app.route('/huescenes')
def hue_scenes():
  text = json.dumps(bridge.scene.get({'which': 'all'}),
                    sort_keys=True, indent=4, separators=(',', ': '))
  resp = Response(text, status=200, mimetype='text/plain')
  return resp

@app.route('/scenes/<scene_name>', methods=['PUT'])
def put_scene(scene_name):
  if scene_name == None:
    return make_response('format: /scenes/<scene>', 400)
  db_set(scene_name, request.get_json())
  return 'OK'

@app.route('/currentscene', methods=['PUT'])
def set_scene():
  scene = request.data

  set_lr_tree_brightness(db_get(scene)['lr_tree'])

  hue_scene = db_get(scene)['hue_scene']
  resource = {
    'which': 0,
    'data': {
      'action': {
        'scene': hue_scene + "-on-0"
      }
    }
  }
  #resource['data']['action'] = {'on': False if scene == "off" else True}
  response = bridge.group.update(resource)
  success = 'success' in response['resource'][0]
  return 'OK' if success else make_response(str(response), 500)

@app.route('/syncscenes', methods=['POST'])
def sync_scenes():
  resp = ''
  hue_scenes = bridge.scene.get({'which': 'all'})['resource']
  scenes = load_db()
  for key, params in scenes.iteritems():
    cur_hs = next(hs for hs in hue_scenes if hs['id'].startswith(params['hue_scene']))
    hue_name = re.match('(.+) on \d', cur_hs['name']).group(1)
    matching_hss = [hs for hs in hue_scenes if hs['name'].startswith(hue_name) and hs['lastupdated']]
    date_for_hs = lambda x: datetime.strptime(x['lastupdated'], '%Y-%m-%dT%H:%M:%S')
    latest_hs = max(matching_hss, key=date_for_hs)
    params['hue_scene'] = re.match('(\w+)-on-\d', latest_hs['id']).group(1)
    resp = resp + key + ': ' + str(latest_hs) + '\n'
    db_set(key, params)
  return resp

### STORAGE: ###

def db_get(key):
  db = load_db()
  return db[key]

def db_set(key, value):
  db = load_db()
  db[key] = value
  save_db(db)

def load_db():
  with open('scenes.json', 'r') as fp:
    return json.load(fp)
  return {}

def save_db(db):
  with open('scenes.json', 'w') as fp:
    json.dump(db, fp, sort_keys=True, indent=4)

setup()

if __name__ == "__main__":
  app.run('0.0.0.0')
