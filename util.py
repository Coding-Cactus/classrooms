import json, random

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