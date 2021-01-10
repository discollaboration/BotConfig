from flask import Flask, render_template, session, request, redirect
from pymongo import MongoClient
from flask_discord import DiscordOAuth2Session
from os import environ as env
from yaml import load, CFullLoader

app = Flask(__name__)
app.config["SECRET_KEY"] = env["SECRET_KEY"].encode("utf-8")

mongo = MongoClient()
database = mongo["BotConfig"]
config_table = database["config"]
config_access_table = database["user_access"]
bot_tokens_table = database["bot_tokens"]
admin_tokens_table = database["admin_tokens"]

env["OAUTHLIB_INSECURE_TRANSPORT"] = "true"
discord = DiscordOAuth2Session(app,
                               client_id=env["DISCORD_CLIENT_ID"],
                               client_secret=env["DISCORD_CLIENT_SECRET"],
                               redirect_uri=env["DISCORD_REDIRECT_URL"])


def has_config_access(guild_id, bot_id):
    if "user_id" not in session.keys():
        if "Authorization" not in request.cookies.keys():
            return False
        splitted = request.cookies["Authorization"].split(" ")
        token_type = splitted[0].lower()
        token = splitted[1]
        if token_type == "bot":
            if bool(bot_tokens_table.find_one({"bot_id": bot_id, "token": token})):
                return True
        elif token_type == "admin":
            if bool(admin_tokens_table.find_one({"token": token})):
                return True
        return False
    access = config_access_table.find_one({"guild_id": guild_id, "user_id": session["user_id"]})
    return bool(access)


@app.route("/guilds/<int:guild_id>/bot/<int:bot_id>")
def render_dashboard(guild_id, bot_id):
    current_config = config_table.find_one({"guild_id": guild_id, "bot_id": bot_id})
    if current_config is None:
        return "Not found", 404
    if not has_config_access(guild_id, bot_id):
        return "No access", 401
    return render_template("bot_config.jinja2", guild_id=guild_id, bot_id=bot_id, config=current_config["raw"])


@app.route("/guilds/<int:guild_id>/bot/<int:bot_id>/update", methods=["POST"])
def update_config(guild_id, bot_id):
    current_config = config_table.find_one({"guild_id": guild_id, "bot_id": bot_id})
    if current_config is None:
        return "Not found", 404
    if not has_config_access(guild_id, bot_id):
        return "No access", 401
    try:
        content = request.data.decode("utf-8")
        config = load(content, Loader=CFullLoader)
    except:
        return "Invalid YML", 400
    config_table.update_one({"guild_id": guild_id, "bot_id": bot_id}, {"$set": {"raw": content, "config": config}})
    return "Ok"


@app.route("/login")
def login():
    return discord.create_session(scope=["identify"], prompt=False)


@app.route("/login/callback")
def login_callback():
    discord.callback()
    user = discord.fetch_user()
    session["user_id"] = user.id
    session["user_name"] = user.username
    return redirect("/")
