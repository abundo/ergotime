#!/usr/bin/env python3

"""
Common utilities

Copyright (C) 2020 Anders Lowinger, anders@abundo.se

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import sys
import os.path
import importlib.machinery
import builtins
import pprint
import datetime
import yaml
from orderedattrdict import AttrDict

import lib.log as log

pp = pprint.PrettyPrinter(indent=4)


class UtilException(Exception):
    pass


def die(msg, exitcode=1):
    print(msg)
    sys.exit(exitcode)


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
        self.savedPath = None

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


def prettyPrint(msg, d):
    if not isinstance(d, (dict, list)):
        try:
            d = vars(d)
        except TypeError:
            pass
    if msg:
        print(msg)
    pp.pprint(d)


def now():
    return datetime.datetime.now().replace(microsecond=0)


def now_str():
    return now().strftime("%Y%m%d%H%M%S")


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=AttrDict):
    """
    Load Yaml document, replace all hashes/mappings with AttrDict
    """
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
        
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def yaml_load(filename):
    with open(filename, "r") as f:
        try:
            # self.default_data = yaml.load(f)
            data = ordered_load(f, yaml.SafeLoader)
            return data
        except yaml.YAMLError as err:
            raise UtilException("Cannot load YAML file %s, err: %s" % (filename, err))
