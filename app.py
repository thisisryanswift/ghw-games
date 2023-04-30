import json, datetime
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from flask_pymongo import PyMongo
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, request

from forms import LeaderboardForm

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

mongo = PyMongo(app, uri=env.get("MONGO_URI"))

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

@app.route("/leaderboard/", methods=["POST"])
def new_leaderboard():
    raw_leaderboard = request.get_json()
    raw_leaderboard["date_added"] = datetime.utcnow()

    leaderboard = Leaderboard(**raw_leaderboard)
    insert_result = leaderboards.insert_one(leaderboard.to_bson())
    print(leaderboard)

    return leaderboard.to_json()

@app.route("/leaderboard/<leaderboard_id>", methods=["GET"])
def get_leaderboard(leaderboard_id):
    leaderboard = leaderboards.find_one_or_404({"_id": ObjectId(leaderboard_id)})
    return Leaderboard(**leaderboard).to_json()

@app.route("/leaderboards/")
def list_leaderboards():
    page = int(request.args.get("page", 1))
    per_page = 10

    cursor = leaderboards.find().sort("name").skip((page - 1) * per_page).limit(per_page)

    leaderboard_count = leaderboards.count_documents({})

    links = {
        "self": {"href": url_for(".list_leaderboards", page=page, _external=True)},
        "last": {
            "href": url_for(".list_leaderboards", page=leaderboard_count // per_page, _external=True)
        },
    }

    if page > 1:
        links["prev"] = {"href": url_for(".list_leaderboards", page=page - 1, _external=True)}

    if page - 1 < leaderboard_count // per_page:
        links["next"] = {"href": url_for(".list_leaderboards", page=page + 1, _external=True)}

    return {
        "leaderboards": [Leaderboard(**leaderboard).to_json() for leaderboard in cursor],
        "_links": links,
    }

@app.route("/")
def home():
    return render_template("home.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))

@app.route("/adduser")
def adduser():
    if session:
        users_collection = mongo.db.users
        users_collection.insert_one(session.get('user'))
    return "Added user"

@app.route("/addleaderboard", methods=["GET", "POST"])
def addleaderboard():
    form = LeaderboardForm()
    if form.is_submitted():
        data = request.form
        leaderboards_collection = mongo.db.leaderboards
        leaderboards_collection.insert_one({"name": data.get("name")})
    return render_template("addleaderboard.html", form=form)

@app.errorhandler(404)
def not_found(e):
    return e, 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 5000))