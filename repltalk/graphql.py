def builtin_to_graphql(item):
	if isinstance(item, list) or isinstance(item, tuple) or isinstance(item, set):
		value = Field(*item)
	elif isinstance(item, dict):
		value = Field(item)
	else:
		value = str(item)
	return value


class Alias():
	def __init__(self, alias, field):
		self.alias = alias
		self.field = field

	def __repr__(self):
		return f'{self.alias}: {self.field}'


def create_args_string(args):
	output = ''
	if args != {}:
		args_tmp = []
		for arg_key in args:
			arg_value = args[arg_key]
			args_tmp.append(f'{arg_key}:{arg_value}')
		output += '('
		output += ','.join(args_tmp)
		output += ')'
	return output


class Field():
	def __init__(self, *args, **kwargs):
		if 'name' in kwargs:
			self.data = ({kwargs['name']: kwargs['data']},)
		elif 'data' in kwargs and len(args) == 1:
			self.data = ({args[0]: kwargs.get('data')},)
		else:
			self.data = args or (kwargs.get('data'),)
		self.args = kwargs.get('args', {})
		# if 'name' not in kwargs and self.args == {}:
		# 	self.args = kwargs

	def __str__(self):
		output = ''

		for item in self.data:
			if isinstance(item, str):
				output += item
				output += create_args_string(self.args)
			elif isinstance(item, Field):
				output += str(item)
				output += create_args_string(self.args)
			elif isinstance(item, Alias):
				output += str(item)
				output += create_args_string(self.args)
			elif isinstance(item, list) or isinstance(item, tuple):
				item_as_graphql = str(builtin_to_graphql(item))
				output += item_as_graphql
				output += create_args_string(self.args)
			elif isinstance(item, Fragment):
				output += item.added_fragment()
			else:
				for field in item:
					value = item[field]
					value = builtin_to_graphql(value)
					output += str(field)
					output += create_args_string(self.args)

					output += '{'
					output += str(value)
					output += '}'
			output += ' '
		if output.endswith(' '):
			output = output[:-1]
		return output

	def __repr__(self):
		return self.__str__()

class Query():
	def __init__(self, name, args, data, fragments=[]):
		self.field = Field({name: data}, args=args)
		self.frags = fragments

	def __str__(self):
		output = 'query ' + str(self.field)
		for frag in self.frags:
			str_frag = frag.fragment_string()
			output += str_frag
		return output


class Mutation():
	def __init__(self, name, args, data):
		self.field = Field({name: data}, args=args)

	def __str__(self):
		return 'mutation ' + str(self.field)


class Fragment():
	def __init__(self, fragment_name, adding_to_name, data):
		self.name = fragment_name
		self.adding_to_name = adding_to_name
		self.field = Field(data)

	def fragment_string(self):
		return f'fragment {self.name} on {self.adding_to_name} { {self.field} }'

	def added_fragment(self):
		return f'...{self.name}'

	def __str__(self):
		return self.added_fragment()
