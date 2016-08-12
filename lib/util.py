#!/usr/bin/env python3

'''
Common utilities
'''

import sys
import os.path
import importlib.machinery
import builtins
import yaml

import lib.log as log

with open("/etc/ergotime/ergotime.yaml", "r") as f:
    try:
        config = yaml.load(f)
        builtins.config = config
    except yaml.YAMLError as err:
        log.error("Cannot load config, err: %s" % err)
        sys.exit(1)

    
class AddSysPath:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.savedPath = sys.path.copy()
        sys.path.insert(0, self.path)

    def __exit__(self, typ, value, tb):
        sys.path = self.savedPath


def importFile(pythonFile):
    dir_name = os.path.dirname(pythonFile)
    module_name = os.path.basename(pythonFile)
    module_name = os.path.splitext(module_name)[0]
    loader = importlib.machinery.SourceFileLoader(module_name, pythonFile)
    with AddSysPath(dir_name):
        return loader.load_module()
