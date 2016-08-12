from flask import render_template
from server import server

@server.route('/')
@server.route('/index')
def index():
    return render_template('index.html')
