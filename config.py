
from xdg import XDG_DATA_HOME
import os

data_path = os.path.join(XDG_DATA_HOME, 'launch64')
if not os.path.exists(data_path):
    os.mkdir(data_path)

repo_path = os.path.join(data_path, 'sm64ex')
repo_exists = os.path.exists(repo_path)

SM64_EU_SHA1 = '8a20a5c83d6ceb0f0506cfc9fa20d8f438cafe51'
SM64_JP_SHA1 = '8a20a5c83d6ceb0f0506cfc9fa20d8f438cafe51'
SM64_SH_SHA1 = '3f319ae697533a255a1003d09202379d78d5a2e0'
SM64_US_SHA1 = '9bef1128717f958171a4afac3ed78ee2bb4e86ce'