from flask import render_template, request, session, flash, redirect
from server import server

@server.route('/')
@server.route('/index')
def home():
    return render_template('index.html')
