from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
from flask_discord import DiscordOAuth2Session
from os import environ as env
from yaml import load, CFullLoader
from session import SessionManager

app = Flask(__name__)
session = SessionManager()
app.config["SECRET_KEY"] = env["SECRET_KEY"].encode("utf-8")

mongo = MongoClient(env["MONGO_URI"])
database = mongo["BotConfig"]
config_table = database["config"]
config_access_table = database["user_access"]
bot_tokens_table = database["bot_tokens"]
admin_tokens_table = database["admin_tokens"]
bot_data_table = database["bot_data"]

env["OAUTHLIB_INSECURE_TRANSPORT"] = "true"
discord = DiscordOAuth2Session(app,
                               client_id=env["DISCORD_CLIENT_ID"],
                               client_secret=env["DISCORD_CLIENT_SECRET"],
                               redirect_uri=env["DISCORD_REDIRECT_URL"])


def is_logged_in():
    return "user_id" in session.keys()


def has_config_access(guild_id, bot_id):
    if "user_id" not in session.keys():
        if "Authorization" not in request.headers.keys():
            return False
        splitted = request.headers["Authorization"].split(" ")
        token_type = splitted[0].lower()
        token = splitted[1]
        if token_type == "bot":
            if bool(bot_tokens_table.find_one({"_id": bot_id, "token": token})):
                return True
        elif token_type == "admin":
            if bool(admin_tokens_table.find_one({"token": token})):
                return True
        return False
    access = config_access_table.find_one({"guild_id": guild_id, "user_id": session["user_id"], "bot_id": bot_id})
    return bool(access)


def verify_access(guild_id, bot_id):
    current_config = config_table.find_one({"guild_id": guild_id, "bot_id": bot_id})
    if current_config is None:
        if not bot_data_table.find_one({"_id": bot_id}):
            return "Not found", 404
        config_table.insert_one({"guild_id": guild_id, "bot_id": bot_id, "config": {}, "raw": ""})
        return verify_access(guild_id, bot_id)
    if not has_config_access(guild_id, bot_id):
        return "No access", 401
    return None, 200


@app.route("/guilds/<int:guild_id>/bot/<int:bot_id>")
def render_dashboard(guild_id, bot_id):
    error, status_code = verify_access(guild_id, bot_id)
    if error is not None:
        return error, status_code
    current_config = config_table.find_one({"guild_id": guild_id, "bot_id": bot_id})
    return render_template("bot_config.jinja2", guild_id=guild_id, bot_id=bot_id, config=current_config["raw"])


@app.route("/guilds/<int:guild_id>/bot/<int:bot_id>/update", methods=["POST"])
def update_config(guild_id, bot_id):
    error, status_code = verify_access(guild_id, bot_id)
    if error is not None:
        return error, status_code
    try:
        content = request.data.decode("utf-8")
        config = load(content, Loader=CFullLoader)
    except:
        return "Invalid YML", 400
    config_table.update_one({"guild_id": guild_id, "bot_id": bot_id}, {"$set": {"raw": content, "config": config}})
    return "Ok"


@app.route("/api/<int:guild_id>/bot/<int:bot_id>/get_config")
def api_get_config(guild_id, bot_id):
    error, status_code = verify_access(guild_id, bot_id)
    if error is not None:
        return error, status_code
    current_config = config_table.find_one({"guild_id": guild_id, "bot_id": bot_id})
    return current_config["config"]


@app.route("/api/<int:guild_id>/bot/<int:bot_id>/grant_access", methods=["POST"])
def api_grant_access(guild_id, bot_id):
    error, status_code = verify_access(guild_id, bot_id)
    if error is not None:
        return error, status_code
    user_id = int(request.data.decode("utf-8"))
    if config_access_table.find_one({"guild_id": guild_id, "user_id": user_id, "bot_id": bot_id}):
        return "Already has access", 400
    config_access_table.insert_one({"guild_id": guild_id, "user_id": user_id, "bot_id": bot_id})
    return "Ok"


@app.route("/api/<int:guild_id>/bot/<int:bot_id>/revoke_access", methods=["POST"])
def api_revoke_access(guild_id, bot_id):
    error, status_code = verify_access(guild_id, bot_id)
    if error is not None:
        return error, status_code
    user_id = int(request.data.decode("utf-8"))
    if not config_access_table.find_one({"guild_id": guild_id, "user_id": user_id, "bot_id": bot_id}):
        return "Doesn't have any access", 400
    config_access_table.delete_one({"guild_id": guild_id, "user_id": user_id, "bot_id": bot_id})
    return "Ok"


@app.route("/guilds")
def render_guilds():
    if not is_logged_in():
        return redirect("/login")
    if "guilds" not in session.keys():
        guilds = discord.fetch_guilds()
        session["guilds"] = [{"id": guild.id, "name": guild.name, "icon_url": guild.icon_url} for guild in guilds]
        guilds = session["guilds"]
    else:
        guilds = session["guilds"]

    config_guilds = []
    for guild in guilds:
        if config_access_table.find_one({"user_id": session["user_id"], "guild_id": guild["id"]}):
            config_guilds.append(guild)
    return render_template("guild_selection.jinja2", guilds=config_guilds)


@app.route("/guilds/<int:guild_id>")
def render_bots_in_guild(guild_id):
    if not is_logged_in():
        return redirect("/login")
    bots = list(config_access_table.find({"user_id": session["user_id"], "guild_id": guild_id}))
    if len(bots) == 0:
        return redirect("/guilds")
    if len(bots) == 1:
        return render_dashboard(guild_id, bots[0]["bot_id"])
    return render_template("bot_selection.jinja2", bots=bots, bot_data_table=bot_data_table, guild_id=guild_id)


@app.route("/login")
def login():
    return discord.create_session(scope=["identify", "guilds"], prompt=False)


@app.route("/login/callback")
def login_callback():
    discord.callback()
    user = discord.fetch_user()
    session["user_id"] = user.id
    session["user_name"] = user.username
    return redirect("/")


@app.route("/")
def gtfo_to_guilds():
    return redirect("/guilds")


if __name__ == '__main__':
    app.run(debug=True)
