import yaml
from threading import Thread

from discover_agent import DiscoverAgent
from device import Device

yaml.add_path_resolver('!devices', ['devices'], dict)
devices = []
discover_thread = None

def discover(devices):
    da = DiscoverAgent(devices)
    da.discover()

with open('config.yaml', 'r') as config_yml:
    try:
        config = yaml.safe_load(config_yml)
        for device in config['devices']:
            devices.append(Device(**device, ip=config['ip']))
        discover_thread = Thread(target = discover, args = (devices, ))
        discover_thread.start()
        discover_thread.join()
    except yaml.YAMLError as exc:
        print (exc)
