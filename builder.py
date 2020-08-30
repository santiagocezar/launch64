from os import stat
from distutils.dir_util import copy_tree
from threading import ThreadError
from config import *

import json
import subprocess as sproc
from threading import Thread

flags_file = data_path + '/buildflags.json'

needs_rebuild = False

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
    global needs_rebuild
    needs_rebuild = True
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
    global needs_rebuild
    needs_rebuild = True
    enabled_flags[flag] = value

def get_raw_flag(flag):
    return enabled_flags[flag]

def set_patch(patch, enabled):
    global needs_rebuild
    needs_rebuild = True
    enabled_patches[patch] = enabled

make: sproc.Popen = None # GNU Make subprocess

def build(callback, *args, **kwargs):
    # Save flags
    json.dump(enabled_flags, open(flags_file, 'w+'))

    def _build_thread(make, callback, *args, **kwargs):
        print(needs_rebuild)
        
        section = lambda msg: f'\033[1m[\033[96m{msg}\033[0m\033[1m]\033[0m'
        error = lambda msg: f'\033[1m\033[91m{msg}\033[0m'

        if needs_rebuild:
            print(section('Restoring repository...'))
            reset = sproc.Popen(['git', 'reset', '--hard'], cwd=repo_path)
            reset = sproc.Popen(['git', 'clean', '-df'], cwd=repo_path)
            reset.wait()

            print(section('Applying patches...'))
            for patch, enabled in enabled_patches.items():
                if enabled:
                    git_apply = sproc.Popen(['git', 'apply', '-p1', patch], cwd=repo_path)
                    result = git_apply.wait()
                    if result != 0:
                        print(error(f'Failed to apply patch \"{patch}\" (exit code {result})'))
                        callback(*args, **kwargs)
                        return

                        

                    
        print(section('Compiling...'))
        make_args = []
        for flag, value in enabled_flags.items():
            make_args.append(f'{flag}={value}')
        make_args.append(f'-j{os.cpu_count()}')

        make = sproc.Popen(['make'] + make_args, cwd=repo_path)
        build_result = make.wait()
        make = None
        
        if build_result != 0:
            print(error(f'Error while compiling (exit code {build_result})'))
            callback(*args, **kwargs)
            return


        print(section('Copying post-build patches...'))
        for file in os.listdir(f'{data_path}/build_dir'):
            copy_tree(f'{data_path}/build_dir/{file}', f'{repo_path}/build/{get_raw_flag("VERSION")}_pc/{file}')

        callback(*args, **kwargs)
        return
    
    thread = Thread(target=_build_thread, args=(make, callback) + args, kwargs=kwargs)
    thread.start()
    return thread

def is_building() -> bool:
    return make is not None

def build_cancel():
    make.kill()
