import os
import util
import time
import asyncio
import repltalk

from PIL import Image

import cloudinary
import cloudinary.api
import cloudinary.uploader

from pymongo import MongoClient

from flask import Flask
from flask import abort
from flask import request
from flask import redirect
from flask import render_template


client = repltalk.Client()

myclient = MongoClient(os.getenv("mongouri"))
mydb = myclient["classrooms"]
user_db = mydb["users"]
classroom_db = mydb["classrooms"]
assignment_db = mydb["assignments"]
invitelinks_db = mydb["invitelinks"]
invitecodes_db = mydb["invitecodes"]

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
		user_id = user.id
		if user_db.find_one({"id": user_id}) == None:
			user_db.insert_one({
				"id": user_id,
				"username": user.name,
				"pfp": user.avatar,
				"first_name": user.first_name,
				"last_name": user.last_name,
				"roles": util.parse_roles(user.roles),
				"classrooms": [],
				"classroomInvites": []
			})


@app.route("/")
def landing():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user = user_db.find_one({"id": user.id})
	
	return render_template(
		"landing.html",
		langs=util.langs,
		users=user_db.find(),
		allClassrooms=list(classroom_db.find()),
		invites=user["classroomInvites"],
		userClassrooms=list(classroom_db.find({"id": {"$in": user["classrooms"]}}))
	)


@app.route("/getmakeclassform")
def getmakeclassform():
	return render_template(
		"create_class.html",
		type="make",
		langs=util.langs,
		pfp_url="https://res.cloudinary.com/codingcactus/image/upload/v1611481743/classrooms/repl_logo_p9bqek.png"
	)


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

	classroom_id = str(util.next_id(classroom_db.find()))
	user = asyncio.run(client.get_user(user))
	user_id = user.id
	user_username = user.name
	user_pfp = user.avatar


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
		filename = classroom_id + "." + classroom_pfp.filename.split(".")[1]
		Image.open(classroom_pfp).convert("RGB").save(filename)
		r = cloudinary.uploader.upload(filename,
			folder = "classrooms/",
			public_id = classroom_id,
			overwrite = True,
			resource_type = "image"				
		)
		cloud_img_url = r["url"].replace("http://", "https://")
		os.remove(filename)

	
	classroom_db.insert_one({
		"id": int(classroom_id),
		"owner_id": user_id,
		"owner_username": user_username,
		"owner_pfp": user_pfp,
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
	})
	user_db.update_one({"id": user_id}, {"$addToSet": {"classrooms": int(classroom_id)}})
	
	return f"/classroom/{classroom_id}/teachers"


@app.route("/geteditclassform", methods=["POST"])
def geteditclassform():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	class_id = request.form.get("classId", None)

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or user_id not in classroom["teachers"]:
		return abort(404)

	return render_template(
		"create_class.html",
		type="edit",
		langs=util.langs,
		name=classroom["name"],
		language=classroom["language"],
		description=classroom["description"],
		pfp_url=classroom["classroom_pfp_url"]
	)


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
	user_id = user.id

	classroom = classroom_db.find_one({"id": int(classroom_id)})

	if len(name.replace(" ", "")) == 0 or not name:
		return "Invalid Name"
	if classroom == None or user_id not in classroom["teachers"]:
		return abort(404)
	if classroom_pfp != None and not util.allowed_file(classroom_pfp.filename):
		return "Invalid File Type"
	if len(description.replace(" ", "")) == 0:
		description = "A " + util.langs[classroom["language"]]["name"] + " classroom"


	if not classroom_pfp:
		cloud_img_url = classroom["classroom_pfp_url"]
	else:
		filename = classroom_id + "." +  classroom_pfp.filename.split(".")[1]
		Image.open(classroom_pfp).convert("RGB").save(filename)
		r = cloudinary.uploader.upload(filename,
			folder = "classrooms/",
			public_id = classroom_id,
			overwrite = True,
			resource_type = "image"				
		)
		cloud_img_url = r["url"].replace("http://", "https://")
		os.remove(filename)

	classroom_db.update_one(
		{ "id": int(classroom_id) },
		{"$set": {
			"name": name,
			"description": description,
			"classroom_pfp_url": cloud_img_url
		}}
	)
	
	return f"/classroom/{classroom_id}/teachers"

@app.route("/getcloneclassform", methods=["POST"])
def cloneform():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	class_id = request.form.get("classId", None)

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or user_id not in classroom["teachers"]:
		return abort(404)

	return render_template(
		"create_class.html",
		type="clone",
		langs=util.langs,
		name=classroom["name"],
		language=classroom["language"],
		description=classroom["description"],
		pfp_url=classroom["classroom_pfp_url"]
	)


@app.route("/cloneclass", methods=["POST"])
def clone():
	form = request.form
	files = request.files
	user = util.verify_headers(request.headers)

	clone_class_id = form.get("classId", None)
	name = form.get("name", None)
	description = form.get("description", None)
	classroom_pfp = files.get("classroom-pfp", None)
	try: Image.open(classroom_pfp)
	except: classroom_pfp = None

	classroom_id = str(util.next_id(classroom_db.find()))
	user = (asyncio.run(client.get_user(user)))
	user_id = user.id
	user_username = user.name
	user_pfp = user.avatar

	if clone_class_id: return abort(404)

	if len(name.replace(" ", "")) == 0 or not name:
		return "Invalid Name"
	if classroom_pfp != None and not util.allowed_file(classroom_pfp.filename):
		return "Invalid File Type"

	clone_classroom = classroom_db.find_one({"id": int(clone_class_id)})
	language = clone_classroom["language"]
	
	
	if len(description.replace(" ", "")) == 0:
		description = "A " + util.langs[language.lower()]["name"] + " classroom"


	if not classroom_pfp:
		cloud_img_url = clone_classroom["classroom_pfp_url"]
	else:
		filename = classroom_id + "." + classroom_pfp.filename.split(".")[1]
		Image.open(classroom_pfp).convert("RGB").save(filename)
		r = cloudinary.uploader.upload(filename,
			folder = "classrooms/",
			public_id = classroom_id,
			overwrite = True,
			resource_type = "image"
		)
		cloud_img_url = r["url"].replace("http://", "https://")
		os.remove(filename)
	
	assignments = []
	assignment_ids = []
	next_id = util.next_id(assignment_db.find())
	loops = 0
	for assignment_id in clone_classroom["assignments"]:
		assignment = dict(assignment_db.find_one({"id": assignment_id}))
		del assignment["_id"]
		assignment["id"] = next_id + loops
		assignment["submissions"] = {}
		assignments.append(assignment)
		assignment_ids.append(next_id + loops)
		loops += 1
	
	assignment_db.insert_many(assignments)
	
	classroom_db.insert_one({
		"id": int(classroom_id),
		"owner_id": user_id,
		"owner_username": user_username,
		"owner_pfp": user_pfp,
		"created": time.time(),
		"name": name,
		"language": language.lower(),
		"description": description,
		"classroom_pfp_url": cloud_img_url,
		"teachers": [user_id],
		"students": [],
		"assignments": assignment_ids,
		"studentInviteLink": None,
		"studentInviteCode": None,
		"teacherInviteLink": None,
		"teacherInviteCode": None
	})
	user_db.update_one({"id": user_id}, {"$addToSet": {"classrooms": int(classroom_id)}})
	
	return f"/classroom/{classroom_id}/teachers"


@app.route("/deleteclassroom", methods=["POST"])
def deleteclassroom():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id

	class_id = request.form.get("class_id", None)

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or user_id != classroom["owner_id"]:
		return abort(404)

	user_db.update_many({"id": {"$in": classroom["students"]}}, {"$pull": {"classrooms": int(class_id)}})
	user_db.update_many({"id": {"$in": classroom["teachers"]}}, {"$pull": {"classrooms": int(class_id)}})

	assignment_db.delete_many({"id": {"$in": classroom["assignments"]}})

	if classroom["studentInviteLink"] != None:
		invitelinks_db.delete_one({"link": classroom["studentInviteLink"]})
		invitecodes_db.delete_one({"code": classroom["studentInviteCode"]})
	if classroom["teacherInviteLink"] != None:
		invitelinks_db.delete_one({"link": classroom["teacherInviteLink"]})
		invitecodes_db.delete_one({"code": classroom["teacherInviteCode"]})

	classroom_db.delete_one({"id": int(class_id)})


	return redirect(base_url)


@app.route("/classroom/<id>")
def get_classroom(id):
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	id = int(id)
	user_id = user.id

	classroom = classroom_db.find_one({"id": id})
	assignments = assignment_db.find({"id": {"$in": classroom["assignments"]}})

	if id in user_db.find_one({"id": user_id})["classrooms"]:
		return render_template(
			"classroom.html",
			userId=user_id,
			classroomId=id,
			assignments=list(assignments),
			classroom=classroom,
			teacher=user_id in classroom["teachers"]
		)
	return abort(404)


@app.route("/classroom/<id>/teachers")
def classroom_settings(id):
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	id = int(id)
	user_id = user.id

	classroom = classroom_db.find_one({"id": id})

	if user_id in classroom["teachers"]:
		return render_template(
			"teachers.html",
			classroomId=id,
			user_id=user_id,
			students=list(user_db.find({"id": {"$in": classroom["students"]}})),
			teachers=list(user_db.find({"id": {"$in": classroom["teachers"]}})),
			assignments=list(assignment_db.find({"id": {"$in": classroom["assignments"]}})),
			classroom=classroom
		)
	return abort(404)


@app.route("/getaddstudentsform", methods=["POST"])
def getaddstudentsform():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	class_id = request.form.get("classId", None)

	classroom = classroom_db.find_one({"id": int(class_id)})

	if not class_id: return abort(404)
	if classroom == None: return abort(404)
	if user_id not in classroom["teachers"]: return abort(404)

	if not classroom["studentInviteLink"]:
		inviteLink = util.randomstr(15)
		while invitelinks_db.find_one({"link": inviteLink}) != None:
			inviteLink = util.randomstr(15)
		classroom_db.update_one({"id": int(class_id)}, {"$set": {"studentInviteLink": inviteLink}})
		invitelinks_db.insert_one({"link": inviteLink, "classroom": int(class_id), "type": "student"})
	else:
		inviteLink = classroom["studentInviteLink"]

	if not classroom["studentInviteCode"]:
		inviteCode = util.randomstr(10)
		while invitecodes_db.find_one({"code": inviteCode}) != None:
			inviteCode = util.randomstr(10)
		classroom_db.update_one({"id": int(class_id)}, {"$set": {"studentInviteCode": inviteCode}})
		invitecodes_db.insert_one({"code": inviteCode, "classroom": int(class_id), "type": "student"})
	else:
		inviteCode = classroom["studentInviteCode"]

	return render_template(
		"add_people.html",
		type="student",
		inviteLink=inviteLink,
		inviteCode=inviteCode
	)


@app.route("/getaddteachersform", methods=["POST"])
def getaddteachersform():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	class_id = request.form.get("classId", None)

	classroom = classroom_db.find_one({"id": int(class_id)})

	if not class_id: return abort(404)
	if classroom == None: return abort(404)
	if user_id not in classroom["teachers"]: return abort(404)

	if not classroom["teacherInviteLink"]:
		inviteLink = util.randomstr(15)
		while invitelinks_db.find_one({"link": inviteLink}):
			inviteLink = util.randomstr(15)
		classroom_db.update_one({"id": int(class_id)}, {"$set": {"teacherInviteLink": inviteLink}})
		invitelinks_db.insert_one({"link": inviteLink, "classroom": int(class_id), "type": "teacher"})
	else:
		inviteLink = classroom["teacherInviteLink"]

	if not classroom["teacherInviteCode"]:
		inviteCode = util.randomstr(10)
		while invitecodes_db.find_one({"code": inviteCode}):
			inviteCode = util.randomstr(10)
		classroom_db.update_one({"id": int(class_id)}, {"$set": {"teacherInviteCode": inviteCode}})
		invitecodes_db.insert_one({"code": inviteCode, "classroom": int(class_id), "type": "teacher"})
	else:
		inviteCode = classroom["teacherInviteCode"]

	return render_template(
		"add_people.html",
		type="teacher",
		inviteLink=inviteLink,
		inviteCode=inviteCode
	)



@app.route("/invite/<inviteLink>")
def invite(inviteLink):
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id

	inviteLink = inviteLink.upper()

	link_doc = invitelinks_db.find_one(({"link": inviteLink}))

	if link_doc != None:
		class_id = link_doc["classroom"]
		classroom = classroom_db.find_one({"id": class_id})
		type = link_doc["type"]
		if user_id not in classroom["teachers"] and user_id not in classroom["students"]:
			classroom_db.update_one({"id": class_id}, {"$addToSet": {f"{type}s": user_id}})
			if type == "student":
				for assignment in assignment_db.find({"id": {"$in": classroom["assignments"]}}):
					submissions = assignment["submissions"]
					submissions[str(user_id)] = {
						"status": "not viewed",
						"repl_url": None,
						"feedback": None
					}
					assignment_db.update_one({"id": assignment["id"]}, {"$set": {"submissions": submissions}})
		ext = ""
		if type == "teacher": ext = "/teachers"
		return redirect(f"{base_url}/classroom/{class_id}{ext}")

	return abort(404)


@app.route("/join", methods=["POST"])
def join():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id

	inviteCode = request.form.get("invite_code", "None").upper()

	code_doc = invitecodes_db.find_one({"code": inviteCode})

	if code_doc != None:
		class_id = code_doc["classroom"]
		classroom = classroom_db.find_one({"id": class_id})
		type = code_doc["type"]
		if user_id not in classroom["teachers"] and user_id not in classroom["students"]:
			classroom_db.update_one({"id": class_id}, {"$addToSet": {f"{type}s": user_id}})
			user_db.update_one({"id": user_id}, {"$addToSet": {"classrooms": class_id}})
			if type == "student":
				for assignment in assignment_db.find({"id": {"$in": classroom["assignments"]}}):
					submissions = assignment["submissions"]
					submissions[str(user_id)] = {
						"status": "not viewed",
						"repl_url": None,
						"feedback": None
					}
					assignment_db.update_one({"id": assignment["id"]}, {"$set": {"submissions": submissions}})
			ext = ""
			if type == "teacher": ext = "/teachers"
			return f"{base_url}/classroom/{class_id}{ext}"
		return "You are already in this classroom"

	return "Invalid Code"


@app.route("/invitestudent", methods=["POST"])
def invitestudent():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	class_id = request.form.get("classId", None)

	student = asyncio.run(client.get_user(request.form.get("username", "")))

	if str(student) == "None":
		return "User not found"

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or user_id not in classroom["teachers"]:
		return abort(404)

	student_id = student.id
	db_student = user_db.find_one({"id": student_id})

	if db_student == None:
		student = {
			"id": student_id,
			"username": student.name,
			"pfp": student.avatar,
			"first_name": student.first_name,
			"last_name": student.last_name,
			"roles": util.parse_roles(student.roles),
			"classrooms": [],
			"classroomInvites": []
		}
		user_db.insert_one(student)
	else:
		student = db_student
	
	if user_id == student_id:
		return "You can't invite yourself"

	if int(class_id) in [i["class_id"] for i in student["classroomInvites"]]:
		return "User has already been invited"

	if student_id in classroom["students"]:
		return "User is already a student in this classroom"

	if student_id in classroom["teachers"]:
		return "User is already a teacher in this classroom"

	owner = user_db.find_one({"id": classroom["owner_id"]})

	user_db.update_one({"id": student_id}, {"$push": {"classroomInvites": {
		"class_id": int(class_id),
		"type": "student",
		"class_name": classroom["name"],
		"owner_username": owner["username"],
		"owner_pfp": owner["pfp"]
	}}})

	return "User has been invited"


@app.route("/inviteteacher", methods=["POST"])
def inviteteacher():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	class_id = request.form.get("classId", None)

	teacher = asyncio.run(client.get_user(request.form.get("username", "")))

	if str(teacher) == "None":
		return "User not found"

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or user_id not in classroom["teachers"]:
		return abort(404)

	teacher_id = teacher.id
	db_teacher = user_db.find_one({"id": teacher_id})

	if db_teacher == None:
		teacher = {
			"id": teacher_id,
			"username": teacher.name,
			"pfp": teacher.avatar,
			"first_name": teacher.first_name,
			"last_name": teacher.last_name,
			"roles": util.parse_roles(teacher.roles),
			"classrooms": [],
			"classroomInvites": []
		}
		user_db.insert_one(teacher)
	else:
		teacher = db_teacher
	
	if user_id == teacher_id:
		return "You can't invite yourself"

	if int(class_id) in [i["class_id"] for i in teacher["classroomInvites"]]:
		return "User has already been invited"

	if teacher_id in classroom["students"]:
		return "User is already a student in this classroom"

	if teacher_id in classroom["teachers"]:
		return "User is already a teacher in this classroom"
		
	owner = user_db.find_one({"id": classroom["owner_id"]})

	user_db.update_one({"id": teacher_id}, {"$push": {"classroomInvites": {
		"class_id": int(class_id),
		"type": "teacher",
		"class_name": classroom["name"],
		"owner_username": owner["username"],
		"owner_pfp": owner["pfp"]
	}}})

	return "User has been invited"


@app.route("/acceptinvite", methods=["POST"])
def accept():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	class_id = request.form.get("classId", None)
	inviteType = request.form.get("type", None)

	if not inviteType:
		return abort(404)

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or user_id in classroom[inviteType+"s"]:
		return abort(404)
	
	user = user_db.find_one({"id": user_id})

	if int(class_id) in [i["class_id"] for i in user["classroomInvites"]]:
		newInvites = []
		for i in user["classroomInvites"]:
			if i["class_id"] != int(class_id):
				newInvites.append(i)
		user_db.update_one({"id": user_id}, {"$set": {"classroomInvites": newInvites}})
	else:
		return abort(404)

	classroom_db.update_one({"id": int(class_id)}, {"$push": {f"{inviteType}s": user_id}})
	user_db.update_one({"id": user_id}, {"$push": {"classrooms": int(class_id)}})

	if inviteType == "student":
		for assignment in assignment_db.find({"id": {"$in": classroom["assignments"]}}):
			submissions = assignment["submissions"]
			submissions[str(user_id)] = {
				"status": "not viewed",
				"repl_url": None,
				"feedback": None
			}
			assignment_db.update_one({"id": assignment["id"]}, {"$set": {"submissions": submissions}})

	return "Success"


@app.route("/declineinvite", methods=["POST"])
def decline():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	class_id = request.form.get("classId", None)
	inviteType = request.form.get("type", None)

	if not inviteType:
		return abort(404)

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or user_id in classroom[inviteType+"s"]:
		return abort(404)
	
	user = user_db.find_one({"id": user_id})

	if int(class_id) in user["classroomInvites"]:
		newInvites = []
		for i in user["classroomInvites"]:
			if i["class_id"] != int(class_id):
				newInvites.append(i)
		user_db.update_one({"id": user_id}, {"$set": {"classroomInvites": newInvites}})
	else:
		return abort(404)

	return "Success"


@app.route("/removestudent", methods=["POST"])
def removestudent():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id

	class_id = request.form.get("class_id", None)
	student_id = request.form.get("student_id", None)

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or int(student_id) not in classroom["students"] or user_id not in classroom["teachers"]:
		return abort(404)

	classroom_db.update_one({"id": int(class_id)}, {"$pull": {"students": int(student_id)}})
	user_db.update_one({"id": int(student_id)}, {"$pull": {"classrooms": int(class_id)}})

	for assignment_id in classroom["assignments"]:
		assignment = assignment_db.find_one({"id": assignment_id})
		del assignment["submissions"][student_id]
		assignment_db.update_one({"id": assignment_id}, {"$set": {"submissions": assignment["submissions"]}})
	
	return "Success"

@app.route("/removeteacher", methods=["POST"])
def removeteacher():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id

	class_id = request.form.get("class_id", None)
	teacher_id = request.form.get("teacher_id", None)

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or teacher_id not in classroom["teachers"] or user_id != classroom["owner_id"] or int(teacher_id) == user_id:
		return abort(404)

	classroom_db.update_one({"id": int(class_id)}, {"$pull": {"teachers": int(teacher_id)}})
	user_db.update_one({"id": int(teacher_id)}, {"$pull": {"classrooms": int(class_id)}})

	return "Success"


@app.route("/getmakeassignmentform", methods=["POST"])
def getmakeassignmentsform():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	class_id = request.form.get("classId", None)

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or user_id not in classroom["teachers"]:
		return abort(404)

	return render_template("create_assignment.html", type="make")


@app.route("/makeassignment", methods=["POST"])
def makeassignment():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	class_id = request.form.get("classId", None)

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or user_id not in classroom["teachers"]:
		return abort(404)

	name = request.form.get("name", None)
	instructions = request.form.get("instructions", None)

	if not name or len(name.replace(" ", "")) == 0:
		return "Invalid Name"
	if not instructions or len(instructions.replace(" ", "")) == 0:
		return "Invalid Instructions"

	submissions = {}
	for student_id in classroom["students"]:
		submissions[str(student_id)] = {
			"status": "not viewed",
			"repl_url": None,
			"feedback": None
		}
	assignment_id = util.next_id(assignment_db.find())
	assignment_db.insert_one({
		"id": assignment_id,
		"name": name,
		"instructions": instructions,
		"modal_answer_url": None,
		"submissions": submissions
	})
	classroom_db.update_one({"id": int(class_id)}, {"$push": {"assignments": assignment_id}})

	return f"/classroom/{class_id}/{assignment_id}"


@app.route("/geteditassignmentform", methods=["POST"])
def geteditassignmentsform():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	class_id = request.form.get("classId", None)
	assignment_id = request.form.get("assignmentId", None)

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or user_id not in classroom["teachers"] or int(assignment_id) not in classroom["assignments"]:
		return abort(404)

	assignment = assignment_db.find_one({"id": int(assignment_id)})

	return render_template(
		"create_assignment.html",
		type="edit",
		name=assignment["name"],
		instructions=assignment["instructions"]
	)


@app.route("/editassignment", methods=["POST"])
def editassignment():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	class_id = request.form.get("classId", None)
	assignment_id = request.form.get("assignmentId", None)

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or user_id not in classroom["teachers"] or int(assignment_id) not in classroom["assignments"]:
		return abort(404)

	name = request.form.get("name", None)
	instructions = request.form.get("instructions", None)

	if not name or len(name.replace(" ", "")) == 0:
		return "Invalid Name"
	if not instructions or len(instructions.replace(" ", "")) == 0:
		return "Invalid Instructions"

	assignment_db.update_one({"id": int(assignment_id)}, {"$set": {"name": name, "instructions": instructions}})

	return f"/classroom/{class_id}/{assignment_id}"



@app.route("/deleteassignment", methods=["POST"])
def deleteassignment():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	class_id = request.form.get("class_id", None)
	assignment_id = request.form.get("assignment_id", None)

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or user_id not in classroom["teachers"] or int(assignment_id) not in classroom["assignments"]:
		return abort(404)

	classroom_db.update_one({"id": int(class_id)}, {"$pull": {"assignments": int(assignment_id)}})
	assignment_db.delete_one({"id": int(assignment_id)})

	return redirect(f"{base_url}/classroom/{class_id}")


@app.route("/setmodalanswer", methods=["POST"])
def setmodalanswer():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	class_id = request.form.get("class_id", None)
	assignment_id = request.form.get("assignment_id", None)
	repl_url = request.form.get("repl_url", None)

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or user_id not in classroom["teachers"] or int(assignment_id) not in classroom["assignments"]:
		return abort(404)

	if not repl_url:
		return "No repl provided"
	
	if repl_url.lower().startswith("http://"):
		repl_url = "https://" + repl_url[7:]

	user = user_db.find_one({"id": user_id})
	
	if (not repl_url.lower().startswith("https://repl.it/@" + user["username"].lower() + "/") and
		not repl_url.lower().startswith("https://replit.com/@" + user["username"].lower() + "/") 
	):
		return "Invalid repl url"
	
	if len(repl_url.lower()[8:].split("/")) != 3:
		return "Invalid repl url"

	repl_url = repl_url.split("#")[0]

	assignment_db.update_one({"id": int(assignment_id)}, {"$set": {"modal_answer_url": repl_url}})
	return "Success"



@app.route("/classroom/<class_id>/<assignment_id>")
def get_assignment(class_id, assignment_id):
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or int(assignment_id) not in classroom["assignments"]:
		return abort(404)

	if user_id in classroom["teachers"]:
		return render_template(
			"teacher_assignments_list.html",
			students=user_db.find({"id": {"$in": classroom["students"]}}),
			class_id=class_id,
			assignment_id=assignment_id,
			classroom=classroom,
			assignment=assignment_db.find_one({"id": int(assignment_id)})
		)

	if user_id in classroom["students"]:
		assignment = assignment_db.find_one({"id": int(assignment_id)})
		if assignment["submissions"][str(user_id)]["status"] == "not viewed":
			submissions = assignment["submissions"]
			submissions[str(user_id)]["status"] = "viewed"
			assignment_db.update_one({"id": int(assignment_id)}, {"$set": {"submissions": submissions}})
		return render_template(
			"assignment.html",
			type="student",
			user_id=user_id,
			class_id=class_id,
			assignment_id=assignment_id,
			classroom=classroom,
			assignment=assignment,
			submission=assignment["submissions"][str(user_id)]
		)
	return abort(404)


@app.route("/setrepl", methods=["POST"])
def setrepl():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	repl_url = request.form.get("repl_url", None)
	class_id = request.form.get("class_id", None)
	assignment_id = request.form.get("assignment_id", None)

	classroom = classroom_db.find_one({"id": int(class_id)})
	assignment = assignment_db.find_one({"id": int(assignment_id)})

	if classroom == None or int(assignment_id) not in classroom["assignments"] or user_id not in classroom["students"] or assignment["submissions"][str(user_id)]["repl_url"] != None:
		return "Invalid"

	if not repl_url:
		return "No repl provided"
	
	if repl_url.lower().startswith("http://"):
		repl_url = "https://" + repl_url[7:]

	user = user_db.find_one({"id": user_id})
	
	if (not repl_url.lower().startswith("https://repl.it/@" + user["username"].lower() + "/") and
		not repl_url.lower().startswith("https://replit.com/@" + user["username"].lower() + "/") 
	):
		return "Invalid repl url"
	
	if len(repl_url.lower()[8:].split("/")) != 3:
		return "Invalid repl url"

	repl_url = repl_url.split("#")[0]

	submissions = assignment["submissions"]
	submissions[str(user_id)]["repl_url"] = repl_url
	submissions[str(user_id)]["status"] = "in progress"
	assignment_db.update_one({"id": int(assignment_id)}, {"$set": {"submissions": submissions}})

	return "Success"

	

@app.route("/submit", methods=["POST"])
def submit():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id	
	class_id = request.form.get("class_id", None)
	assignment_id = request.form.get("assignment_id", None)

	classroom = classroom_db.find_one({"id": int(class_id)})
	assignment = assignment_db.find_one({"id": int(assignment_id)})

	if classroom == None or user_id not in classroom["students"] or int(assignment_id) not in classroom["assignments"] or assignment["submissions"][str(user_id)]["status"] != "in progress":
		return abort(404)

	submissions = assignment["submissions"]
	submissions[str(user_id)]["status"] = "awaiting feedback"
	assignment_db.update_one({"id": int(assignment_id)}, {"$set": {"submissions": submissions}})

	return redirect(f"{base_url}/classroom/{class_id}")
	
	
@app.route("/unsubmit", methods=["POST"])
def unsubmit():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	
	class_id = request.form.get("class_id", None)
	assignment_id = request.form.get("assignment_id", None)

	classroom = classroom_db.find_one({"id": int(class_id)})
	assignment = assignment_db.find_one({"id": int(assignment_id)})

	if classroom == None or user_id not in classroom["students"] or int(assignment_id) not in classroom["assignments"] or assignment["submissions"][user_id]["status"] != "awaiting feedback":
		return abort(404)

	submissions = assignment["submissions"]
	submissions[str(user_id)]["status"] = "in progress"
	assignment_db.update_one({"id": int(assignment_id)}, {"$set": {"submissions": submissions}})

	return redirect(f"{base_url}/classroom/{class_id}")

@app.route("/resubmit", methods=["POST"])
def resubmit():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id
	
	class_id = request.form.get("class_id", None)
	assignment_id = request.form.get("assignment_id", None)

	classroom = classroom_db.find_one({"id": int(class_id)})
	assignment = assignment_db.find_one({"id": int(assignment_id)})

	if classroom == None or user_id not in classroom["students"] or int(assignment_id) not in classroom["assignments"] or assignment["submissions"][str(user_id)]["status"] != "returned":
		return abort(404)

	submissions = assignment["submissions"]
	submissions[str(user_id)]["status"] = "awaiting feedback"
	assignment_db.update_one({"id": int(assignment_id)}, {"$set": {"submissions": submissions}})

	return redirect(f"{base_url}/classroom/{class_id}")



@app.route("/classroom/<class_id>/<assignment_id>/<student_id>")
def view_students_submission(class_id, assignment_id, student_id):
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id

	classroom = classroom_db.find_one({"id": int(class_id)})

	if classroom == None or int(student_id) not in classroom["students"] or int(assignment_id) not in classroom["assignments"]:
		return abort(404)

	if user_id not in classroom["teachers"]:
		return abort(404)

	assignment = assignment_db.find_one({"id": int(assignment_id)})

	return render_template(
		"assignment.html",
		type="teacher",
		class_id=int(class_id),
		student_id=int(student_id),
		assignment_id=int(assignment_id),
		classroom=classroom,
		assignment=assignment,
		submission=assignment["submissions"][str(student_id)]
	)


@app.route("/sendfeedback", methods=["POST"])
def sendfeedback():
	user = asyncio.run(client.get_user(util.verify_headers(request.headers)))
	user_id = user.id

	class_id = request.form.get("class_id", None)
	student_id = request.form.get("student_id", None)
	assignment_id = request.form.get("assignment_id", None)
	feedback = request.form.get("feedback", None)

	classroom = classroom_db.find_one({"id": int(class_id)})
	assignment = assignment_db.find_one({"id": int(assignment_id)})	

	if classroom == None or int(student_id) not in classroom["students"] or int(assignment_id) not in classroom["assignments"] or assignment["submissions"][str(student_id)]["status"] not in ["awaiting feedback", "returned"]:
		return abort(404)

	if user_id not in classroom["teachers"]:
		return abort(404)

	submissions = assignment["submissions"]
	submissions[str(student_id)]["feedback"] = feedback
	submissions[str(student_id)]["status"] = "returned"
	assignment_db.update_one({"id": int(assignment_id)}, {"$set": {"submissions": submissions}})

	return redirect(f"{base_url}/classroom/{class_id}/{assignment_id}")


@app.route("/favicon.ico")
def favicon():
	return redirect("https://repl.it/public/images/favicon.ico")


util.loop_refresh()
app.run("0.0.0.0")