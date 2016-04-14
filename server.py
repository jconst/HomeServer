#!/usr/bin/env python
import requests
import json
import shelve
from beautifulhue.api import Bridge
from flask import Flask, Response, request, make_response

app = Flask(__name__)
app.config['DEBUG'] = True

def setup():
  global bridge
  bridge = create_bridge()

def create_bridge():
  bridge_addr = discover_bridge_ip()
  bridge = Bridge(device={'ip':bridge_addr}, 
                  user={'name':'2bb6465d7c479351631cd18e4daad16f'})
  return bridge

def discover_bridge_ip():
  resp = requests.get('https://www.meethue.com/api/nupnp')
  return resp.json()[0]['internalipaddress']

def set_lr_tree_brightness(brightness):
  pass
  # ip = get_db()['lr_tree_ip']
  # requests.get(ip + '?b=' + brightness)

### ROUTES: ###

@app.route('/')
def list_scenes():
  return make_response(str(get_db()), 200)

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
  get_db()[scene_name] = request.get_json()
  return 'OK'

@app.route('/currentscene', methods=['PUT'])
def set_scene():
  scene = request.data

  set_lr_tree_brightness(get_db()[scene]['lr_tree'])

  hue_scene = get_db()[scene]['hue_scene']
  resource = {
    'which': 0,
    'data': {
      'action': {
        'scene': hue_scene + "-on-0"
      }
    }
  }
  if scene == 'off':
    resource['data']['action'] = {'on': False}
  response = bridge.group.update(resource)
  success = 'success' in response['resource'][0]
  return 'OK' if success else make_response(str(response), 500)

@app.route('/living-room-ip', methods=['PUT'])
def set_living_room_ip():
  get_db()['lr_tree_ip'] = request.data
  return 'OK'

def get_db():
  db = shelve.open('scenes.db')

setup()

if __name__ == "__main__":
  app.run()
