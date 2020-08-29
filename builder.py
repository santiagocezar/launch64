from os import stat
from threading import ThreadError
from config import *

import json
import subprocess as sproc
from threading import Thread

flags_file = data_path + '/buildflags.json'

enabled_flags = {
    'BETTERCAMERA': 0,
    'NODRAWINGDISTANCE': 0,
    'TEXTURE_FIX': 0,
    'EXT_OPTIONS_MENU': 1,
    'TEXTSAVES': 0,
    'EXTERNAL_DATA': 0,
    'DISCORDRPC': 0,
    'VERSION': 'us'
}

enabled_patches = {}

try:
    enabled_flags.update(json.load(open(flags_file)))
except FileNotFoundError:
    pass

def set_boolean_flag(flag, state):
    print('Setting', flag, 'to', int(state))
    enabled_flags[flag] = int(state)

def get_boolean_flag(flag) -> bool:
    state = enabled_flags.get(flag)
    print(flag, state)
    if state is None:
        return False
    if type(state) is not int:
        return False
    return bool(state)

def set_raw_flag(flag, value):
    enabled_flags[flag] = value

def get_raw_flag(flag):
    return enabled_flags[flag]

def set_patch(patch, enabled):
    pass

make: sproc.Popen = None # GNU Make subprocess

def build(callback, *args, **kwargs):
    cmd_args = []
    for flag, value in enabled_flags.items():
        cmd_args.append(f'{flag}={value}')
    cmd_args.append(f'-j{os.cpu_count()}')
    # Save flags
    json.dump(enabled_flags, open(flags_file, 'w+'))

    def _build_thread(make, callback, *args, **kwargs):
        make = sproc.Popen(['/bin/make'] + cmd_args, cwd=repo_path)
        make.wait()
        callback(*args, **kwargs)
        make = None
        return
    
    thread = Thread(target=_build_thread, args=(make, callback) + args, kwargs=kwargs)
    thread.start()
    return thread

def is_building() -> bool:
    return make is not None

def build_cancel():
    make.kill()
