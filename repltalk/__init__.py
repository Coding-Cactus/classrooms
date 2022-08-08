import aiohttp
from datetime import datetime
from repltalk.queries import Queries
import warnings

# Bots approved by the Repl.it Team (or me) that are allowed to log in
# (100% impossible to hack yes definitely)
whitelisted_bots = {
	'repltalk',
	'admin@allseeingbot.com',
	'r4idtheweb',
	'replpedia',
	'codingcactus'
}

base_url = 'https://replit.com'


class ReplTalkException(Exception): pass


class NotWhitelisted(ReplTalkException): pass


class AlreadyReported(ReplTalkException): pass


class BoardDoesntExist(ReplTalkException): pass


class GraphqlError(ReplTalkException): pass


class DeletedError(ReplTalkException): pass


class InvalidLogin(ReplTalkException): pass


class PostNotFound(ReplTalkException): pass


class Repl():
	__slots__ = ('id', 'embed_url', 'url', 'title', 'language')

	def __init__(
		self, data
	):
		# Grab the attributes from the data object
		self.id = data['id']
		self.embed_url = data['embedUrl']
		self.url = data['hostedUrl']
		self.title = data['title']
		self.language = Language(
			data['lang']
		)

	def __repr__(self):
		return f'<{self.title}>'

	def __eq__(self, repl2):
		return self.id == repl2.id

	def __hash__(self):
		return hash((self.id, self.url, self.title))


# A LazyPost contains more limited information about the post
# so it doesn't include things like comments
class LazyPost():
	__slots__ = ('client', 'data', 'url', 'id', 'content', 'author', 'title')

	def __init__(self, client, data):
		self.client = client
		self.data = data

		self.url = data['url']
		self.id = data['id']
		self.content = data['body']
		self.author = User(client, data['user'])
		self.title = data['title']
	
	async def delete(self):
		client = self.client
		r = await client.perform_graphql(
			'deletePost',
			Queries.delete_post,
			id=self.id,
		)
		return r

	async def get_full_post(self):
		return await self.client.get_post(self.id)


# A LazyComment contains limited information about the comment,
# so it doesn't include things like replies
class LazyComment():
	def __init__(self, client, data):
		self.client = client
		self.url = data['url']
		self.id = data['id']
		self.content = data['body']
		self.author = User(client, data['user'])
		
	async def delete(self):
		client = self.client
		r = await client.perform_graphql(
			'deleteComment',
			Queries.delete_comment,
			id=self.id,
		)
		return r

	async def get_full_comment(self):
		return await self.client.get_comment(self.id)


class Report:
	__slots__ = (
		'id', 'reason', 'resolved', 'timestamp',
		'creator', 'post', 'type', 'client', 'deleted'
	)

	def __init__(self, client, data):

		self.id = data['id']
		self.type = data['type']
		self.reason = data['reason']
		self.resolved = data['resolved']
		self.timestamp = data['timeCreated']  # Should this be parsed? if so, fix test_report_get_attached test
		self.creator = User(client, data['creator'])
		self.client = client
		self.deleted = False
		# There are two types of reports, post reports and comment reports.
		if data['post']:
			self.type = 'post'
			self.post = LazyPost(client, data['post'])
		elif data['comment']:
			self.type = 'comment'

			self.post = LazyComment(client, data['comment'])
		else:
			raise DeletedError('Post is already deleted')

	def __str__(self):
		url = self.post.url
		if 'https://repl.it' in url:
			url = url.replace('https://repl.it', '')
		return f'<Report for {url}>'

	async def get_attached(self):
		if isinstance(self.post, (LazyPost, LazyComment)):
			if self.type == 'post':
				self.post = await self.post.get_full_post()
			else:
				self.post = await self.post.get_full_comment()
		return self.post
	
	async def resolve(self):
		await self.client._resolve_report(self.id)


class LazyReport:
	__slots__ = ('client', 'id', 'reason', 'deleted', 'creator')

	def __init__(self, client, data):
		self.client = client
		self.id = data['id']
		self.reason = data['reason']
		self.creator = User(client, data['creator'])
		self.deleted = True

	def __str__(self):
		url = 'DELETED'
		return f'<Report for {url}>'

	async def get_attached(self):
		return self

	async def resolve(self):
		await self.client._resolve_report(self.id)

	async def get_full_comment(self):
		return await self.client._get_repor


class ReportList():
	__slots__ = (
		'client', 'refresh', 'resolved', 'reports', 'i'
	)

	def __init__(self, client, data):
		self.reports = []
		for r in data:
			try:
				self.reports.append(Report(client, r))
			except DeletedError:
				self.reports.append(LazyReport(client, r))

	def __iter__(self):
		self.i = 0
		return self

	def __next__(self):
		if self.i >= len(self.reports):
			raise StopIteration
		self.i += 1
		return self.reports[self.i - 1]

	def __aiter__(self):
		self.i = 0
		return self

	async def __anext__(self):
		if self.i >= len(self.reports):
			raise StopAsyncIteration
		self.i += 1
		await self.reports[self.i - 1].get_attached()
		return self.reports[self.i - 1]


class AsyncPostList():
	__slots__ = (
		'i', 'client', 'sort', 'search', 'after', 'limit', 'posts_queue', 'board'
	)

	def __init__(
		self, client, board, limit=32, sort='new', search='', after=None
	):
		self.i = 0
		self.client = client

		self.sort = sort
		self.search = search
		self.after = after

		self.limit = limit
		self.posts_queue = []

		self.board = board

	def __aiter__(self):
		return self

	async def __anext__(self):
		if self.i >= self.limit:
			raise StopAsyncIteration
		if len(self.posts_queue) == 0:
			new_posts = await self.board._get_posts(
				sort=self.sort,
				search=self.search,
				after=self.after
			)
			self.posts_queue.extend(new_posts['items'])
			self.after = new_posts['pageInfo']['nextCursor']
		current_post_raw = self.posts_queue.pop(0)
		current_post = get_post_object(self.client, current_post_raw)

		self.i += 1

		return current_post

	def __await__(self):
		post_list = PostList(
			client=self.client,
			posts=[],
			board=self.board,
			after=self.after,
			sort=self.sort,
			search=self.search
		)
		return post_list.next().__await__()


class PostList(list):
	__slots__ = ('posts', 'after', 'board', 'sort', 'search', 'i', 'client')

	def __init__(self, client, posts, board, after, sort, search):
		self.posts = posts
		self.after = after
		self.board = board
		self.sort = sort
		self.search = search
		self.client = client
		warnings.warn(
			'Doing await get_posts is deprecated, '
			'use async for post in get_posts instead.',
			DeprecationWarning
		)

	def __iter__(self):
		self.i = 0
		return self

	def __next__(self):
		self.i += 1
		if self.i >= len(self.posts):
			raise StopIteration
		return self.posts[self.i]

	def __str__(self):
		if len(self.posts) > 30:
			return f'<{len(self.posts)} posts>'
		return str(self.posts)

	def __getitem__(self, indices):
		return self.posts[indices]

	async def next(self):
		new_posts = await self.board._get_posts(
			sort=self.sort,
			search=self.search,
			after=self.after
		)
		posts = [
			get_post_object(self.client, post_raw) for post_raw in new_posts['items']
		]
		self.after = new_posts['pageInfo']['nextCursor']
		self.posts = posts
		return self

	def __eq__(self, postlist2):
		return self.board == postlist2.board

	def __ne__(self, postlist2):
		return self.board != postlist2.board


class CommentList(list):
	__slots__ = ('post', 'comments', 'after', 'board', 'sort', 'search', 'i')

	def __init__(self, post, comments, board, after, sort):
		self.post = post
		self.comments = comments
		self.after = after
		self.board = board
		self.sort = sort

	def __iter__(self):
		self.i = 0
		return self

	def __next__(self):
		self.i += 1
		if self.i >= len(self.posts):
			raise StopIteration
		return self.comments[self.i]

	def __str__(self):
		if len(self.comments) > 30:
			return f'<{len(self.comments)} comments>'
		return str(self.comments)

	async def next(self):
		post_list = await self.board.comments(
			sort=self.sort,
			search=self.search,
			after=self.after
		)
		self.comments = post_list.comments
		self.board = post_list.board
		self.after = post_list.after
		self.sort = post_list.sort
		self.search = post_list.search

	def __eq__(self, commentlist2):
		return self.post == commentlist2.post

	def __ne__(self, commentlist2):
		return self.post != commentlist2.post


class Comment():
	__slots__ = (
		'client', 'id', 'content', 'timestamp', 'can_edit', 'can_comment',
		'can_report', 'has_reported', 'path', 'url', 'votes', 'can_vote',
		'has_voted', 'author', 'post', 'replies', 'parent'
	)

	def __init__(
		self, client, data, post, parent=None
	):
		self.client = client
		self.id = data['id']
		self.content = data.get('body')
		if self.content is None:
			return
		timestamp = data['timeCreated']
		self.timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
		self.can_edit = data['canEdit']
		self.can_comment = data['canComment']
		self.can_report = data['canReport']
		self.has_reported = data['hasReported']
		self.path = data['url']
		self.url = base_url + data['url']
		self.votes = data['voteCount']
		self.can_vote = data['canVote']
		self.has_voted = data['hasVoted']
		self.parent = parent
		user = data['user']

		if user is not None:
			user = User(
				client,
				user=user
			)
		self.author = user
		self.post = post  # Should already be a post object

		raw_replies = data.get('comments', [])
		replies = []

		for inner_reply in raw_replies:
			replies.append(Comment(
				self.client,
				data=inner_reply,
				post=self.post,
				parent=self
			))
		self.replies = replies

	def __repr__(self):
		if len(self.content) > 100:
			return repr(self.content[:100] + '...')
		else:
			return repr(self.content)

	def __eq__(self, post2):
		return self.id == post2.id

	def __ne__(self, post2):
		return self.id != post2.id

	async def reply(self, content):
		c = await self.client.perform_graphql(
			'createComment',
			Queries.create_comment,
			input={
				'body': content,
				'commentId': self.id,
				'postId': self.post.id
			}
		)
		c = c['comment']
		return Comment(
			self.client,
			data=c,
			post=self.post,
			parent=self
		)

	async def report(self, reason):
		client = self.client
		r = await client.perform_graphql(
			'createBoardReport',
			Queries.create_report,
			commentId=self.id,
			reason=reason,
			show_errors=False
		)
		if not r:
			raise AlreadyReported('This comment has already been reported by this account.')
		return r
	
	async def delete(self):
		client = self.client
		r = await client.perform_graphql(
			'deleteComment',
			Queries.delete_comment,
			id=self.id,
		)
		return r
	
	def __hash__(self):
		return hash((self.id, self.content, self.votes, self.replies))


class Board():
	__slots__ = ('client', 'name', )

	def __init__(self, client):
		self.client = client

	async def _get_posts(self, sort, search, after):
		return await self.client._posts_in_board(
			board_slugs=[self.name],
			order=sort,
			search_query=search,
			after=after
		)

	def get_posts(self, sort='top', search='', limit=32, after=None):
		if sort == 'top':
			sort = 'votes'
		return AsyncPostList(
			self.client,
			limit=limit,
			sort=sort,
			search=search,
			after=after,
			board=self
		)

	async def create_post(  # TODO
		self, title: str, content: str, repl: Repl = None, show_hosted=False
	):
		pass

	def __repr__(self):
		return f'<{self.name} board>'

	def __hash__(self):
		return hash((self.name,))


class RichBoard(Board):  # a board with more stuff than usual
	__slots__ = (
		'client', 'id', 'url', 'name', 'slug', 'title_cta', 'body_cta',
		'button_cta', 'name', 'repl_required', 'data'
	)

	def __init__(
		self, client, data
	):
		self.client = client
		self.data = data

		self.id = data['id']
		self.url = base_url + data['url']
		self.name = data['name']
		self.slug = data['slug']
		self.body_cta = data['bodyCta']
		self.title_cta = data['titleCta']
		self.button_cta = data['buttonCta']

	def __eq__(self, board2):
		return self.id == board2.id and self.name == board2.name

	def __ne__(self, board2):
		return self.id != board2.id or self.name != board2.name

	def __hash__(self):
		return hash((
			self.id,
			self.name,
			self.slug,
			self.body_cta,
			self.title_cta,
			self.button_cta
		))


class Language():
	__slots__ = (
		'id', 'display_name', 'key', 'category', 'is_new', 'icon', 'icon_path',
		'tagline'
	)

	def __init__(
		self, data
	):
		self.id = data['id']
		self.display_name = data['displayName']
		self.key = data['key']  # identical to id???
		self.category = data['category']
		self.tagline = data['tagline']
		self.is_new = data['isNew']
		icon = data['icon']
		self.icon_path = icon
		if icon and icon[0] == '/':
			icon = 'https://repl.it' + icon
		self.icon = icon

	def __str__(self):
		return self.display_name

	def __repr__(self):
		return f'<{self.id}>'

	def __eq__(self, lang2):
		return self.key == lang2.key

	def __ne__(self, lang2):
		return self.key != lang2.key

	def __hash__(self):
		return hash((
			self.id,
			self.display_name,
			self.key,
			self.category,
			self.tagline,
			self.icon_path
		))


def get_post_object(client, post):
	return Post(
		client, data=post
	)


class Post():
	__slots__ = (
		'client', 'id', 'title', 'content', 'is_announcement', 'path', 'url',
		'board', 'timestamp', 'can_edit', 'can_comment', 'can_pin', 'can_set_type',
		'can_report', 'has_reported', 'is_locked', 'show_hosted', 'votes',
		'can_vote', 'has_voted', 'author', 'repl', 'answered', 'can_answer',
		'pinned', 'comment_count', 'language', 'vote_list', 'data'
	)

	def __init__(
		self, client, data
	):
		self.client = client
		self.data = data

		self.id = data['id']
		self.title = data['title']
		self.content = data['body']
		self.is_announcement = data['isAnnouncement']
		self.path = data['url']
		self.url = base_url + data['url']
		board = RichBoard(
			client=client,
			data=data['board']
		)
		self.board = board
		timestamp = data['timeCreated']
		self.timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
		self.can_edit = data['canEdit']
		self.can_comment = data['canComment']
		self.can_pin = data['canPin']
		self.can_set_type = data['canSetType']
		self.can_report = data['canReport']
		self.has_reported = data['hasReported']
		self.is_locked = data['isLocked']
		self.show_hosted = data['showHosted']
		self.votes = data['voteCount']
		self.vote_list = data['votes']['items']

		self.can_vote = data['canVote']
		self.has_voted = data['hasVoted']

		user = data['user']
		if user is not None:
			user = User(
				client,
				user=user
			)
		self.author = user

		repl = data['repl']
		if repl is None:
			self.repl = None
			self.language = None
		else:
			self.repl = Repl(repl)
			self.language = self.repl.language
		self.answered = data['isAnswered']
		self.can_answer = data['isAnswerable']
		self.pinned = data['isPinned']
		self.comment_count = data['commentCount']

	def __repr__(self):
		return f'<{self.title}>'

	def __eq__(self, post2):
		return self.id == post2.id

	def __ne__(self, post2):
		return self.id != post2.id

	async def report(self, reason):
		client = self.client
		r = await client.perform_graphql(
			'createBoardReport',
			Queries.create_report,
			postId=self.id,
			reason=reason,
			show_errors=False
		)
		if not r:
			raise AlreadyReported('This post has already been reported by this account.')
		return r
	
	async def delete(self):
		client = self.client
		r = await client.perform_graphql(
			'deletePost',
			Queries.delete_post,
			id=self.id,
		)
		return r

	async def get_comments(self, order='new'):
		_comments = await self.client._get_comments(
			self.id,
			order
		)
		comments = []
		for c in _comments['comments']['items']:
			comments.append(Comment(
				self.client,
				data=c,
				post=self
			))
		return comments

	async def post_comment(self, content):
		c = await self.client.perform_graphql(
			'createComment',
			Queries.create_comment,
			input={
				'body': content,
				'postId': self.id
			}
		)
		c = c['comment']
		return Comment(
			client=self.client,
			data=c,
			post=self,
		)

	def __hash__(self):
		return hash((
			self.id,
			self.title,
			self.content
		))


class User():
	__slots__ = (
		'client', 'data', 'id', 'name', 'avatar', 'url', 'cycles', 'roles',
		'full_name', 'first_name', 'last_name', 'is_logged_in',
		'bio', 'is_hacker', 'languages', 'timestamp', 'data'
	)

	def __init__(
		self, client, user
	):
		self.client = client
		self.data = user

		self.id = user['id']
		self.name = user['username']
		self.avatar = user['image']
		self.url = user['url']
		self.roles = user['roles']
		self.is_hacker = user['isHacker']

		self.full_name = user['fullName']
		self.first_name = user['firstName']
		self.last_name = user['lastName']

		time_created = user['timeCreated']
		self.timestamp = datetime.strptime(time_created, '%Y-%m-%dT%H:%M:%S.%fZ')

		self.is_logged_in = user['isLoggedIn']
		self.bio = user['bio']
		# Convert all of the user's frequently used
		# languages into Language objects
		self.languages = [
			Language(language) for language in user['languages']
		]

	async def get_comments(self, limit=30, order='new'):
		client = self.client
		_comments = await client._get_user_comments(
			self.id,
			limit,
			order
		)
		comments = []
		for c in _comments['comments']['items']:

			comments.append(Comment(
				client,
				data=c,
				post=c['post']['id']
			))

		return comments

	async def get_posts(self, limit=30, order='new'):
		client = self.client
		_posts = await client._get_user_posts(
			self.id,
			limit,
			order
		)

		posts = []
		for p in _posts['posts']['items']:

			posts.append(Post(
				client,
				data=p
			))

		return posts

	async def get_repls(
		self, limit=30,
		pinned_first=False,
		before=None,
		after=None,
		direction=None
	):
		repls = await self.client._get_user_repls(
			self,
			limit,
			pinned_first, before,
			after, direction,
		)
		public_repls_data = repls['publicRepls']

		repl_list_raw = public_repls_data['items']

		repl_list = [Repl(r) for r in repl_list_raw]
		return repl_list
	
	async def ban(self, reason):
		client = self.client
		r = await client.perform_graphql(
			'Mutation',
			Queries.ban_user,
			user=self.name,
			reason=reason,
		)
		return r

	def __repr__(self):
		return f'<{self.name}>'

	def __eq__(self, user2):
		return self.id == user2.id

	def __ne__(self, user2):
		return self.id != user2.id

	def __hash__(self):
		return hash((
			self.id,
			self.name,
			self.full_name,
			self.bio
		))


class Leaderboards():
	__slots__ = (
		'limit', 'iterated', 'users', 'raw_users', 'next_cursor', 'client'
	)

	def __init__(self, client, limit):
		self.limit = limit
		self.iterated = 0
		self.users = []
		self.raw_users = []
		self.next_cursor = None
		self.client = client

	def __await__(self):
		return self.load_all().__await__()

	def __aiter__(self):
		return self

	def __next__(self):
		raise NotImplementedError

	async def load_all(self):
		async for _ in self: _
		return self.users

	async def __anext__(self):
		ended = len(self.users) + 1 > self.limit
		if self.iterated <= len(self.users) and not ended:
			self.iterated += 30
			leaderboard = await self.client._get_leaderboard(
				self.next_cursor
			)
			self.next_cursor = leaderboard['pageInfo']['nextCursor']
			self.raw_users.extend(leaderboard['items'])

		if ended:
			raise StopAsyncIteration
		user = self.raw_users[len(self.users)]
		user = User(
			self,
			user=user
		)

		self.users.append(user)
		return user

	def __repr__(self):
		if self.iterated >= self.limit:
			return f'<top {self.limit} leaderboard users (cached)>'
		return f'<top {self.limit} leaderboard users>'

	def __str__(self):
		return self.__repr__()


class Client():
	__slots__ = ('default_ref', 'default_requested_with', 'sid', 'boards')

	def __init__(self):
		self.default_ref = base_url + '/@mat1/repl-talk-api'
		self.default_requested_with = 'ReplTalk'
		self.sid = None
		self.boards = self._boards(self)

	async def perform_graphql(
		self,
		operation_name,
		query,
		ignore_none=False,
		show_errors=True,
		**variables,
	):
		payload = {
			'operationName': operation_name,
			'query': str(query)
		}
		if ignore_none:
			payload['variables'] = {q: variables[q] for q in variables if q is not None}
		else:
			payload['variables'] = variables

		async with aiohttp.ClientSession(
			cookies={'connect.sid': self.sid},
			headers={
				'referer': self.default_ref,
				'X-Requested-With': self.default_requested_with
			}
		) as s:
			async with s.post(
				base_url + '/graphql',
				json=payload
			) as r:
				data = await r.json()
		if 'data' in data:
			data = data['data']
		if data is None:
			if show_errors:
				print('ERROR:', await r.json())
			return None
		keys = data.keys()
		if len(keys) == 1:
			data = data[next(iter(keys))]
		if isinstance(data, list):

			try:
				loc = data[0]['locations'][0]['column']
				print(str(query)[:loc-1] + '!!!!!' + str(query)[loc-1:])
			except KeyError:
				pass
		return data

	async def login(self, username, password):
		if username.lower() not in whitelisted_bots:
			raise NotWhitelisted(
				f'{username} is not whitelisted and therefore is not allowed to log in.\n'
				'Please ask mat#6207 if you would like to be added to the whitelist.'
			)

		async with aiohttp.ClientSession(
			headers={'referer': self.default_ref}
		) as s:
			async with s.post(
				base_url + '/login',
				json={
					'username': username,
					'password': password,
					'teacher': False
				},
				headers={
					'X-Requested-With': username
				}
			) as r:
				if await r.text() == '{"message":"Invalid username or password."}':
					raise InvalidLogin('Invalid username or password.')
				# Gets the connect.sid cookie
				connectsid = str(dict(r.cookies)['connect.sid'].value)
				self.sid = connectsid
			return self

	async def _get_reports(self, resolved):
		reports = await self.perform_graphql(
			'boardReports',
			Queries.get_reports,
			unresolvedOnly=not resolved
		)
		ids = [r['id'] for r in reports if 'id' in r]
		lazy_reports = await self.perform_graphql(
			'boardReports',
			Queries.get_lazy_reports,
			unresolvedOnly=not resolved
		)
		for lr in lazy_reports:
			if lr['id'] not in ids:
				reports.append(lr)
		return reports

	async def get_reports(self, resolved=False):
		raw_data = await self._get_reports(resolved)
		return ReportList(self, raw_data)

	async def _get_post(self, post_id):
		post = await self.perform_graphql(
			'post', Queries.get_post, id=int(post_id), votesCount=100
		)
		if post is None:
			raise PostNotFound(f'Post id {post_id} is invalid')
		return post

	async def get_post(self, post_id):
		post = await self._get_post(post_id)
		return get_post_object(self, post)

	async def post_exists(self, post_id):
		if isinstance(post_id, Post):
			post_id = post_id.id
		post = await self.perform_graphql(
			'post', Queries.post_exists, id=post_id
		)
		return post is not None

	async def _get_leaderboard(self, cursor=None):
		if cursor is None:
			leaderboard = await self.perform_graphql(
				'leaderboard',
				Queries.get_leaderboard
			)
		else:
			leaderboard = await self.perform_graphql(
				'leaderboard',
				Queries.get_leaderboard,
				after=cursor
			)
		return leaderboard

	def get_leaderboard(self, limit=30):
		return Leaderboards(self, limit)

	async def _resolve_report(self, id):
		return await self.perform_graphql(
			'resolveBoardReport',
			Queries.resolve_report,
			id=id
		)

	async def _get_all_posts(
		self, order='new', search_query=None, after=None
	):
		posts = await self.perform_graphql(
			'ReplPostsFeed',
			Queries.posts_feed,
			options={
				'order': order.title(),
				'searchQuery': search_query,
				'after': after
			}			
		)
		return posts

	async def get_user_by_id(self, user_id):
		return User(
			self,
			await self.perform_graphql(
				'user',
				Queries.get_user_by_id,
				user_id=user_id
			)
		)

	async def _posts_in_board(
		self,
		board_slugs=None,
		order='new',
		search_query=None,
		after=None
	):
		posts = await self.perform_graphql(
			'ReplPostsFeed',
			Queries.posts_feed,
			options={
				'boardSlugs': board_slugs,
				'order': order.title(),
				'searchQuery': search_query,
				'after': after
			}			
		)
		return posts

	class _boards:
		board_names = ['all', 'announcements', 'challenge', 'ask', 'learn', 'share', 'templates', 'tutorials']
		__slots__ = ['client', ] + board_names
		for board in board_names:
			locals()['_' + board] = type(
				'_' + board,
				(Board,),
				{'name': board}
			)
			# Creates classes for each of the boards
		del board	 # Don't want that extra class var

		def __init__(self, client):
			self.client = client

			self.all = self._all(client)
			self.announcements = self._announcements(client)
			self.challenge = self._challenge(client)
			self.ask = self._ask(client)
			self.learn = self._learn(client)
			self.share = self._share(client)
			self.templates = self._templates(client)
			self.tutorials = self._tutorials(client)

	async def _get_comments(self, post_id, order='new'):
		return await self.perform_graphql(
			'post',
			Queries.get_comments,
			id=post_id,
			commentsOrder=order
		)

	async def _get_user_comments(self, user_id, limit, order):

		return await self.perform_graphql(
			'ProfileComments',
			Queries.get_user_comments,
			user_id=user_id,
			limit=limit,
			commentsOrder=order
		)

	async def _get_user_posts(self, user_id, limit, order):
		return await self.perform_graphql(
			'user',
			Queries.get_user_posts,
			user_id=user_id,
			limit=limit,
			order=order
		)

	async def _get_user_repls(
		self, user, limit,
		pinned_first, before,
		after, direction
	):
		return await self.perform_graphql(
			'user',
			Queries.get_user_repls,
			user_id=user.id,
			limit=limit,
			pinnedFirst=pinned_first,
			before=before,
			after=after,
			direction=direction
		)

	async def _get_all_comments(self, order='new'):
		return await self.perform_graphql(
			'comments',
			Queries.get_all_comments,
			order=order
		)

	async def _get_comment(self, id):
		return await self.perform_graphql(
			'comment',
			Queries.get_comment,
			id=id
		)

	async def get_comment(self, id):
		data = await self._get_comment(id)
		post = await self.get_post(data['post']['id'])
		return Comment(self, data, post)

	async def get_all_comments(self, order='new'):
		_comments = await self._get_all_comments(order=order)
		comments = []
		for c in _comments['items']:
			comments.append(Comment(
				self,
				id=c['id'],
				body=c['body'],
				time_created=c['timeCreated'],
				can_edit=c['canEdit'],
				can_comment=c['canComment'],
				can_report=c['canReport'],
				has_reported=c['hasReported'],
				url=c['url'],
				votes=c['voteCount'],
				can_vote=c['canVote'],
				has_voted=c['hasVoted'],
				user=c['user'],
				post=c['post'],
				comments=c['comments']
			))
		return comments

	async def _get_user(self, name):
		user = await self.perform_graphql(
			'userByUsername',
			Queries.get_user,
			username=name,
		)
		return user

	async def get_user(self, name):
		user = await self._get_user(name)
		if user is None:
			return None
		u = User(
			self,
			user=user
		)
		return u
