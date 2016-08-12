#!/usr/bin/env python3

import sys, yaml
with open("/etc/ergotime/ergotime.yaml", "r") as f:
    try:
        config = yaml.load(f)
    except yaml.YAMLError as err:
        print("Cannot load config, err: %s" % err)
        sys.exit(1)
sys.path.insert(0, config['basedir'] )


from server import server

# app.config['myconf'] = config

server.run(host='0.0.0.0', debug=True)
