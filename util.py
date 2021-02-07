import json, random, os, easypydb, repltalk, asyncio, threading

db = easypydb.DB("db", os.getenv("dbToken"))

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
	db.load()
	for user_id in db["users"]:
		user = await client.get_user_by_id(int(user_id))
		if str(user) != "None":
			db["users"][user_id]["username"] = user.name
			db["users"][user_id]["pfp"] = user.avatar
			db["users"][user_id]["first_name"] = user.first_name
			db["users"][user_id]["last_name"] = user.last_name
			db["users"][user_id]["roles"] = parse_roles(user.roles)
			db.save()
		await asyncio.sleep(10)


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
		if (int(id)) > biggest:
			biggest = int(id)
	return biggest+1