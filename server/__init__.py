import datetime

from flask import Flask, Response, request, redirect, render_template, flash, abort
from flask.json import JSONEncoder
from flask.ext.login import LoginManager, UserMixin, login_required, login_user, logout_user

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
server.secret_key="ergotime 12343432434"

login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view="login"

# proxy for a database of users

#    "admin": ("Löwinger", "Anders"),
#    "anders": ("Löwinger", "Anders"),
#    "lise": ("Löwinger", "Liselotte"),
#

class User(UserMixin):

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_id(self):
        return str(self.username)

user_database = {}
user_database["admin"] = User("admin", "password")

@login_manager.user_loader
def load_user(username):
    print("load_user", username)
    if username in user_database:
        return user_database[username]
    return None

@server.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        if request.form['password'] == 'p' and request.form['username'] == 'admin':
            user = User(request.form['username'], request.form["password"])
            print("user", user)
            login_user(user)
            flash("Logged in as user " + request.form["username"])
            print("Logged in as user " + request.form["username"])
            return redirect(request.args.get("next", "/"))
        return abort(401)
    else:
        return render_template('login.html')

@server.route("/logout")
def logout():
    logout_user()
    print("Logged out")
    flash("Logged out")
    return Response("Logged out")


from server.controller import default
from server.controller import activity
from server.controller import reports
from server.controller import table_crud
from server.controller import api
