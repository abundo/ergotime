import datetime

from flask import Flask
from flask.json import JSONEncoder

class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return JSONEncoder.default(self, obj)


server = Flask(__name__, 
            static_url_path = "/static",
            static_folder = "/opt/ergotime/server/static",
            template_folder = '/opt/ergotime/server/views',
        )
server.json_encoder = CustomJSONEncoder


from server.controller import default
from server.controller import reports
from server.controller import table_crud
from server.controller import api
