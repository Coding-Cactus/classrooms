import json, random, os, repltalk, asyncio, threading, pymongo

myclient = pymongo.MongoClient(os.getenv("mongouri"))
mydb = myclient["classrooms"]
user_db = mydb["users"]

def verify_headers(headers):
    name = headers.get("X-Replit-User-Name")

    if name:
        return name
    else:
        return None

def parse_roles(roles):
	parsedRoles = []
	for role in roles:
		parsedRoles.append(role['name'])
	return parsedRoles


with open("static/languages.json") as f:
	langs = json.load(f)


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', "gif"}
def allowed_file(filename):
    return '.' in filename and (filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)


def randomstr(num):
	s = ""
	for i in range(num):
		s += chr(random.choice([random.randint(48, 57), random.randint(65, 90)]))
	return s

client = repltalk.Client()

async def refresh_user_info():
	for db_user in list(user_db.find()):
		try:
			id = db_user["id"]
			user = await client.get_user_by_id(id)
			if str(user) != "None":
				user_db.update_one({"id": id}, {"$set": {
					"username": user.name,
					"pfp": user.avatar,
					"first_name": user.first_name,
					"last_name": user.last_name,
					"roles": parse_roles(user.roles)
				}})
				await asyncio.sleep(10)
		except TypeError:
			continue


def loop_refresh():
	def func_wrapper():
		loop_refresh()
		asyncio.run(refresh_user_info())
	t = threading.Timer(600, func_wrapper)
	t.start()
	return t

def next_id(ids):
	biggest = 0
	for id in ids:
		if id["id"] > biggest:
			biggest = id["id"]
	return biggest+1