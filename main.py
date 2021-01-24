import os
import util
import time
import asyncio
import repltalk

from PIL import Image

from easypydb import DB

import cloudinary
import cloudinary.api
import cloudinary.uploader

from flask import Flask
from flask import abort
from flask import request
from flask import redirect
from flask import render_template


client = repltalk.Client()

db = DB("db", os.getenv("dbToken"))

cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


@app.before_request
def before_request():
	if "/static/" not in request.path:
		if not util.verify_headers(request.headers):
			return render_template("login.html")
	
	user = util.verify_headers(request.headers)
	if user:
		user = asyncio.run(client.get_user(user))
		user_id = str(user.id)
		db.load()
		if user_id not in db["users"]:
			db["users"][user_id] = {
				"username": user.name,
				"pfp": user.avatar,
				"first_name": user.first_name,
				"last_name": user.last_name,
				"roles": util.parse_roles(user.roles),
				"classrooms": []
			}
			db.save()


@app.route("/")
def landing():
	head = request.headers
	user = util.verify_headers(head)
	
	user_id = str(asyncio.run(client.get_user(user)).id)
	db.load()
	return render_template("landing.html", teacher=("teacher" in db["users"][user_id]["roles"]), allClassrooms=db["classrooms"], userClassrooms=db["users"][user_id]["classrooms"], users=db["users"], langs=util.langs)


@app.route("/getmakeclassform")
def getmakeclassform():
	return render_template("create_class.html", langs=util.langs)


@app.route("/createclass", methods=["POST"])
def make_class():
	form = request.form
	files = request.files
	user = util.verify_headers(request.headers)

	name = form.get("name", None)	
	language = form.get("language", None)
	description = form.get("description", None)
	classroom_pfp = files.get("classroom-pfp", None)
	try: Image.open(classroom_pfp)
	except: classroom_pfp = None

	classroom_id = str(len(db["classrooms"]) + 1)
	user = (asyncio.run(client.get_user(user)))
	user_id = str(user.id)
	user_username = user.name


	if len(name.replace(" ", "")) == 0 or not name:
		return "Invalid Name"
	if language.lower() not in util.langs:
		return "Invalid Language"
	if classroom_pfp != None and not util.allowed_file(classroom_pfp.filename):
		return "Invalid File Type"
	if len(description.replace(" ", "")) == 0:
		description = "A " + util.langs[language.lower()]["name"] + " classroom"


	if not classroom_pfp:
		cloud_img_url = "https://res.cloudinary.com/codingcactus/image/upload/v1611481743/classrooms/repl_logo_p9bqek.png"
	else:
		Image.open(classroom_pfp).save(classroom_id+".png")
		r = cloudinary.uploader.upload(classroom_id+".png",
			folder = "classrooms/",
			public_id = classroom_id,
			overwrite = True,
			resource_type = "image"				
		)
		cloud_img_url = r["url"].replace("http://", "https://")
		os.remove(classroom_id+".png")

	
	db.load()
	db["classrooms"][classroom_id] = {
		"owner_id": user_id,
		"owner_username": user_username,
		"created": time.time(),
		"name": name,
		"language": language.lower(),
		"description": description,
		"classroom_pfp_url": cloud_img_url,
		"teachers": [user_id],
		"students": [],
		"assignments": [],
	}
	db["users"][user_id]["classrooms"].append(classroom_id)
	db.save()
	
	return f"/classroom/{classroom_id}/teachers"


@app.route("/classroom/<id>")
def get_classroom(id):
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)

	if id in db["users"][user_id]["classrooms"]:
		return render_template("classroom.html", classroom=db["classrooms"][id])
	return abort(404)


@app.route("/classroom/<id>/teachers")
def classroom_settings(id):
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)

	if id in db["users"][user_id]["classrooms"] and user_id in db["classrooms"][id]["teachers"]:
		return render_template("teachers.html", classroom=db["classrooms"][id])
	return abort(404)





@app.route("/favicon.ico")
def favicon():
	return redirect("https://repl.it/public/images/favicon.ico")


app.run("0.0.0.0")