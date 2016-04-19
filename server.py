#!/usr/bin/env python
import requests
import json
import shelve
from beautifulhue.api import Bridge
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
  pass
  # ip = get_db()['lr_tree_ip']
  # requests.get(ip + '?b=' + brightness)

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

@app.route('/living-room-ip', methods=['PUT'])
def set_living_room_ip():
  db_set('lr_tree_ip', request.data)
  return 'OK'

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
  with open('scenes-out.json', 'w') as fp:
    json.dumps(db, fp, sort_keys=True, indent=4)

setup()

if __name__ == "__main__":
  app.run('0.0.0.0')
