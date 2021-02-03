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

base_url = "https://classrooms.codingcactus.repl.co"


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
				"classrooms": [],
				"classroomInvites": []
			}
			db.save()


@app.route("/")
def landing():
	head = request.headers
	user = util.verify_headers(head)
	
	user_id = str(asyncio.run(client.get_user(user)).id)
	db.load()
	return render_template("landing.html", teacher=("teacher" in db["users"][user_id]["roles"]), allClassrooms=db["classrooms"], userClassrooms=db["users"][user_id]["classrooms"], users=db["users"], langs=util.langs, invites=db["users"][user_id]["classroomInvites"])


@app.route("/getmakeclassform")
def getmakeclassform():
	return render_template("create_class.html", type="make", pfp_url="https://res.cloudinary.com/codingcactus/image/upload/v1611481743/classrooms/repl_logo_p9bqek.png", langs=util.langs)


@app.route("/makeclass", methods=["POST"])
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
	teacher = "teacher" in util.parse_roles(user.roles)

	if not teacher: return abort(404)


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
		filename = classroom_pfp.filename
		Image.open(classroom_pfp).save(filename)
		r = cloudinary.uploader.upload(filename,
			folder = "classrooms/",
			public_id = classroom_id,
			overwrite = True,
			resource_type = "image"				
		)
		cloud_img_url = r["url"].replace("http://", "https://")
		os.remove(filename)

	
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
		"studentInviteLink": None,
		"studentInviteCode": None,
		"teacherInviteLink": None,
		"teacherInviteCode": None
	}
	db["users"][user_id]["classrooms"].append(classroom_id)
	db.save()
	
	return f"/classroom/{classroom_id}/teachers"


@app.route("/geteditclassform", methods=["POST"])
def geteditclassform():
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)
	class_id = request.form.get("classId", None)

	if class_id not in db["classrooms"] or user_id not in db["classrooms"][class_id]["teachers"]:
		return abort(404)

	classroom = db["classrooms"][class_id]

	return render_template("create_class.html", type="edit", name=classroom["name"], language=classroom["language"], description=classroom["description"], pfp_url=classroom["classroom_pfp_url"], langs=util.langs)


@app.route("/editclass", methods=["POST"])
def edit_class():
	form = request.form
	files = request.files
	user = util.verify_headers(request.headers)

	name = form.get("name", None)
	classroom_id = form.get("classId", None)
	description = form.get("description", None)
	classroom_pfp = files.get("classroom-pfp", None)
	try: Image.open(classroom_pfp)
	except: classroom_pfp = None

	user = (asyncio.run(client.get_user(user)))
	user_id = str(user.id)

	if len(name.replace(" ", "")) == 0 or not name:
		return "Invalid Name"
	if classroom_id not in db["classrooms"] or user_id not in db["classrooms"][classroom_id]["teachers"]:
		return abort(404)
	if classroom_pfp != None and not util.allowed_file(classroom_pfp.filename):
		return "Invalid File Type"
	if len(description.replace(" ", "")) == 0:
		description = "A " + util.langs[db["classrooms"][classroom_id]["language"]]["name"] + " classroom"


	if not classroom_pfp:
		cloud_img_url = db["classrooms"][classroom_id]["classroom_pfp_url"]
	else:
		filename = classroom_pfp.filename
		Image.open(classroom_pfp).save(filename)
		r = cloudinary.uploader.upload(filename,
			folder = "classrooms/",
			public_id = classroom_id,
			overwrite = True,
			resource_type = "image"				
		)
		cloud_img_url = r["url"].replace("http://", "https://")
		os.remove(filename)

	
	db.load()
	db["classrooms"][classroom_id]["name"] = name
	db["classrooms"][classroom_id]["description"] = description
	db["classrooms"][classroom_id]["classroom_pfp_url"] = cloud_img_url
	db.save()
	
	return f"/classroom/{classroom_id}/teachers"


@app.route("/classroom/<id>")
def get_classroom(id):
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)

	if id in db["users"][user_id]["classrooms"]:
		return render_template("classroom.html", userId=user_id, teacher=(user_id in db["classrooms"][id]["teachers"]), classroomId=id, classroom=db["classrooms"][id], users=db["users"], assignments=db["assignments"])
	return abort(404)


@app.route("/classroom/<id>/teachers")
def classroom_settings(id):
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)

	if id in db["users"][user_id]["classrooms"] and user_id in db["classrooms"][id]["teachers"]:
		return render_template("teachers.html", classroom=db["classrooms"][id], classroomId=id, users=db["users"])
	return abort(404)


@app.route("/getaddstudentsform", methods=["POST"])
def getaddstudentsform():
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)
	class_id = request.form.get("classId", None)

	if not class_id: return abort(404)
	if user_id not in db["classrooms"][class_id]["teachers"]: return abort(404)

	if not db["classrooms"][class_id]["studentInviteLink"]:
		inviteLink = util.randomstr(15)
		while inviteLink in db["studentInviteLinks"] or inviteLink in db["teacherInviteLinks"]:
			inviteLink = util.randomstr(15)
		db["classrooms"][class_id]["studentInviteLink"] = inviteLink
		db["studentInviteLinks"][inviteLink] = class_id
		db.save()
	else:
		inviteLink = db["classrooms"][class_id]["studentInviteLink"]

	if not db["classrooms"][class_id]["studentInviteCode"]:
		inviteCode = util.randomstr(10)
		while inviteCode in db["studentInviteCodes"]:
			inviteCode = util.randomstr(10)
		db["classrooms"][class_id]["studentInviteCode"] = inviteCode
		db["studentInviteCodes"][inviteCode] = class_id
		db.save()
	else:
		inviteCode = db["classrooms"][class_id]["studentInviteCode"]

	return render_template("add_people.html", type="student", inviteLink=inviteLink, inviteCode=inviteCode)


@app.route("/getaddteachersform", methods=["POST"])
def getaddteachersform():
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)
	class_id = request.form.get("classId", None)

	if not class_id: return abort(404)
	if class_id not in db["classrooms"]: return abort(404)
	if user_id not in db["classrooms"][class_id]["teachers"]: return abort(404)

	if not db["classrooms"][class_id]["teacherInviteLink"]:
		inviteLink = util.randomstr(15)
		while inviteLink in db["teacherInviteLinks"] or inviteLink in db["studentInviteLinks"]:
			inviteLink = util.randomstr(15)
		db["classrooms"][class_id]["teacherInviteLink"] = inviteLink
		db["teacherInviteLinks"][inviteLink] = class_id
		db.save()
	else:
		inviteLink = db["classrooms"][class_id]["teacherInviteLink"]

	if not db["classrooms"][class_id]["teacherInviteCode"]:
		inviteCode = util.randomstr(10)
		while inviteCode in db["teacherInviteCodes"]:
			inviteCode = util.randomstr(10)
		db["classrooms"][class_id]["teacherInviteCode"] = inviteCode
		db["teacherInviteCodes"][inviteCode] = class_id
		db.save()
	else:
		inviteCode = db["classrooms"][class_id]["teacherInviteCode"]

	return render_template("add_people.html", type="teacher", inviteLink=inviteLink, inviteCode=inviteCode)



@app.route("/invite/<inviteLink>")
def invite(inviteLink):
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)

	if inviteLink in db["studentInviteLinks"]:
		class_id = db["studentInviteLinks"][inviteLink]
		if user_id not in db["classrooms"][class_id]["students"]:
			db["classrooms"][class_id]["students"].append(user_id)
			db["users"][user_id]["classrooms"].append(class_id)
			for assignment in db["classrooms"][class_id]["assignments"]:
				db["assignments"][assignment]["submissions"][user_id] = {
					"status": "not viewed",
					"repl_url": None,
					"feedback": None
				}
			db.save()
		return redirect(f"{base_url}/classroom/{class_id}")

	if inviteLink in db["teacherInviteLinks"] and "teacher" in util.parse_roles(user.roles):
		class_id = db["teacherInviteLinks"][inviteLink]
		if user_id not in db["classrooms"][class_id]["teachers"]:
			db["classrooms"][class_id]["teachers"].append(user_id)
			db["users"][user_id]["classrooms"].append(class_id)
		return redirect(f"{base_url}/classroom/{class_id}/teachers")

	return abort(404)


@app.route("/join", methods=["POST"])
def join():
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)

	inviteCode = request.form.get("invite_code", "None").upper()

	if inviteCode in db["studentInviteCodes"]:
		class_id = db["studentInviteCodes"][inviteCode]
		if user_id not in db["classrooms"][class_id]["students"]:
			db["classrooms"][class_id]["students"].append(user_id)
			db["users"][user_id]["classrooms"].append(class_id)
			for assignment in db["classrooms"][class_id]["assignments"]:
				db["assignments"][assignment]["submissions"][user_id] = {
					"status": "not viewed",
					"repl_url": None,
					"feedback": None
				}
			db.save()
		return redirect(f"{base_url}/classroom/{class_id}")

	if inviteCode in db["teacherInviteCodes"] and "teacher" in util.parse_roles(user.roles):
		class_id = db["teacherInviteCodes"][inviteCode]
		if user_id not in db["classrooms"][class_id]["teachers"]:
			db["classrooms"][class_id]["teachers"].append(user_id)
			db["users"][user_id]["classrooms"].append(class_id)
			db.save()
		return redirect(f"{base_url}/classroom/{class_id}/teachers")

	return "Invalid Code"


@app.route("/invitestudent", methods=["POST"])
def invitestudent():
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)
	class_id = request.form.get("classId", None)

	student = asyncio.run(client.get_user(request.form.get("username", "")))

	if str(student) == "None":
		return "User not found"

	if not class_id or class_id not in db["classrooms"] or user_id not in db["classrooms"][class_id]["teachers"]:
		return abort(404)

	student_id = str(student.id)

	if student_id not in db["users"]:
		db["users"][student_id] = {
			"username": student.name,
			"pfp": student.avatar,
			"first_name": student.first_name,
			"last_name": student.last_name,
			"roles": util.parse_roles(student.roles),
			"classrooms": [],
			"classroomInvites": []
		}
		db.save()
	
	if user_id == class_id:
		return "You can't invite yourself"

	if class_id in db["users"][student_id]["classroomInvites"]:
		return "User has already been invited"

	if student_id in db["classrooms"][class_id]["students"]:
		return "User is already a student in this classroom"

	db["users"][student_id]["classroomInvites"].append({
		"class_id": class_id,
		"type": "student"
	})
	db.save()

	return "User has been invited"


@app.route("/inviteteacher", methods=["POST"])
def inviteteacher():
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)
	class_id = request.form.get("classId", None)

	teacher = asyncio.run(client.get_user(request.form.get("username", "")))

	if str(teacher) == "None":
		return "User not found"

	if not class_id or class_id not in db["classrooms"] or user_id not in db["classrooms"][class_id]["teachers"]:
		return abort(404)

	teacher_id = str(teacher.id)

	if teacher_id not in db["users"]:
		db["users"][teacher_id] = {
			"username": teacher.name,
			"pfp": teacher.avatar,
			"first_name": teacher.first_name,
			"last_name": teacher.last_name,
			"roles": util.parse_roles(teacher.roles),
			"classrooms": [],
			"classroomInvites": []
		}
		db.save()
	
	if user_id == class_id:
		return "You can't invite yourself"

	if "teacher" not in db["users"][teacher_id]["roles"]:
		return "User is not a teacher"

	if class_id in db["users"][teacher_id]["classroomInvites"]:
		return "User has already been invited"

	if teacher_id in db["classrooms"][class_id]["teachers"]:
		return "User is already a teacher in this classroom"

	db["users"][teacher_id]["classroomInvites"].append({
		"class_id": class_id,
		"type": "teacher"
	})
	db.save()

	return "User has been invited"


@app.route("/acceptinvite", methods=["POST"])
def accept():
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)
	class_id = request.form.get("classId", None)
	inviteType = request.form.get("type", None)

	if not inviteType:
		return abort(404)

	if not class_id or class_id not in db["classrooms"] or user_id in db["classrooms"][class_id][inviteType+"s"]:
		return abort(404)
	
	
	found = False
	for invite in db["users"][user_id]["classroomInvites"]:
		if class_id == invite["class_id"]:
			db["users"][user_id]["classroomInvites"].remove(invite)
			found = True
			break

	if not found:
		return abort(404)

	db["classrooms"][class_id][inviteType+"s"].append(user_id)
	db["users"][user_id]["classrooms"].append(class_id)
	if inviteType == "student":
		for assignment in db["classrooms"][class_id]["assignments"]:
			db["assignments"][assignment]["submissions"][user_id] = {
				"status": "not viewed",
				"repl_url": None,
				"feedback": None
			}
	db.save()

	return "Success"


@app.route("/declineinvite", methods=["POST"])
def decline():
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)
	class_id = request.form.get("classId", None)
	inviteType = request.form.get("type", None)

	if not inviteType:
		return abort(404)

	if not class_id or class_id not in db["classrooms"] or user_id in db["classrooms"][class_id][inviteType+"s"]:
		return abort(404)
	
	found = False
	for invite in db["users"][user_id]["classroomInvites"]:
		if class_id == invite["class_id"]:
			db["users"][user_id]["classroomInvites"].remove(invite)
			found = True
			break		
	db.save()

	if not found:
		return abort(404)

	return "Success"



@app.route("/getmakeassignmentform", methods=["POST"])
def getmakeassignmentsform():
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)
	class_id = request.form.get("classId", None)

	if class_id not in db["classrooms"] or user_id not in db["classrooms"][class_id]["teachers"]:
		return abort(404)

	return render_template("create_assignment.html", type="make")


@app.route("/makeassignment", methods=["POST"])
def makeassignment():	
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)
	class_id = request.form.get("classId", None)

	if class_id not in db["classrooms"] or user_id not in db["classrooms"][class_id]["teachers"]:
		return abort(404)

	name = request.form.get("name", None)
	instructions = request.form.get("instructions", None)

	if not name or len(name.replace(" ", "")) == 0:
		return "Invalid Name"
	if not instructions or len(instructions.replace(" ", "")) == 0:
		return "Invalid Instructions"

	assignment_id = str(len(db["assignments"]) + 1)
	db["assignments"][assignment_id] = {
		"name": name,
		"instructions": instructions,
		"submissions": {}
	}
	for student_id in db["classrooms"][class_id]["students"]:
		db["assignments"][assignment_id]["submissions"][student_id] = {
			"status": "not viewed",
			"repl_url": None,
			"feedback": None
		}		
	db["classrooms"][class_id]["assignments"].append(assignment_id)
	db.save()

	return f"/classroom/{class_id}/{assignment_id}"


@app.route("/classroom/<class_id>/<assignment_id>")
def get_assignment(class_id, assignment_id):
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)

	if class_id not in db["classrooms"] or assignment_id not in db["classrooms"][class_id]["assignments"]:
		return abort(404)

	if user_id in db["classrooms"][class_id]["teachers"]:
		return render_template("teacher_assignments_list.html", classroom=db["classrooms"][class_id], assignment=db["assignments"][assignment_id], users=db["users"], assignment_id=assignment_id)
	if user_id in db["classrooms"][class_id]["students"]:
		if db["assignments"][assignment_id]["submissions"][user_id]["status"] == "not viewed":
			db["assignments"][assignment_id]["submissions"][user_id]["status"] = "viewed"
			db.save()
		return render_template("assignment.html", user_id=user_id, classroom=db["classrooms"][class_id], assignment=db["assignments"][assignment_id], submission=db["assignments"][assignment_id]["submissions"][user_id], class_id=class_id, assignment_id=assignment_id)
	return abort(404)


@app.route("/setrepl", methods=["POST"])
def setrepl():
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)
	repl_url = request.form.get("repl_url", None)
	class_id = request.form.get("class_id", None)
	assignment_id = request.form.get("assignment_id", None)
	if class_id not in db["classrooms"] or assignment_id not in db["classrooms"][class_id]["assignments"] or user_id not in db["classrooms"][class_id]["students"] or db["assignments"][assignment_id]["submissions"][user_id]["repl_url"] != None:
		return "Invalid"

	if not repl_url:
		return "No repl provided"
	
	if repl_url.lower().startswith("http://"):
		repl_url = "https://" + repl_url[7:]
	
	if not repl_url.lower().startswith("https://repl.it/@" + db["users"][user_id]["name"].lower() + "/"):
		return "Invalid repl url"
	
	if len(repl_url.lower()[8:].split("/")) != 3:
		return "Invalid repl url"

	repl_url = repl_url.split("#")[0]

	db["assignments"][assignment_id]["submissions"][user_id]["repl_url"] = repl_url
	db["assignments"][assignment_id]["submissions"][user_id]["status"] = "in progress"
	db.save()

	return "Success"

	

@app.route("/submit", methods=["POST"])
def submit():
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)
	
	class_id = request.form.get("class_id", None)
	assignment_id = request.form.get("assignment_id", None)

	if class_id not in db["classrooms"] or user_id not in db["classrooms"][class_id]["students"] or assignment_id not in db["classrooms"][class_id]["assignments"] or db["assignments"][assignment_id]["submissions"][user_id]["status"] != "in progress":
		return abort(404)

	db["assignments"][assignment_id]["submissions"][user_id]["status"] = "awaiting feedback"
	db.save()

	return redirect(f"{base_url}/classroom/{class_id}")
	
	
@app.route("/unsubmit", methods=["POST"])
def unsubmit():
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)
	
	class_id = request.form.get("class_id", None)
	assignment_id = request.form.get("assignment_id", None)

	if class_id not in db["classrooms"] or user_id not in db["classrooms"][class_id]["students"] or assignment_id not in db["classrooms"][class_id]["assignments"] or db["assignments"][assignment_id]["submissions"][user_id]["status"] != "awaiting feedback":
		return abort(404)

	db["assignments"][assignment_id]["submissions"][user_id]["status"] = "in progress"
	db.save()

	return redirect(f"{base_url}/classroom/{class_id}")

@app.route("/resubmit", methods=["POST"])
def resubmit():
	db.load()
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = str(user.id)
	
	class_id = request.form.get("class_id", None)
	assignment_id = request.form.get("assignment_id", None)

	if class_id not in db["classrooms"] or user_id not in db["classrooms"][class_id]["students"] or assignment_id not in db["classrooms"][class_id]["assignments"] or db["assignments"][assignment_id]["submissions"][user_id]["status"] != "sent back":
		return abort(404)

	db["assignments"][assignment_id]["submissions"][user_id]["status"] = "awaiting feedback"
	db.save()

	return redirect(f"{base_url}/classroom/{class_id}")



@app.route("/classroom/<class_id>/<assignment_id>/<student_id>")
def view_students_submission(class_id, assignment_id, student_id):
	return "not implemented yet :("



@app.route("/favicon.ico")
def favicon():
	return redirect("https://repl.it/public/images/favicon.ico")


util.loop_refresh()
app.run("0.0.0.0")