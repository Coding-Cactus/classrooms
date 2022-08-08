from repltalk import graphql

# query: query post($id: Int!, $after: String) {
#   post(id: $id) {
#     ...PostVotesVotes
#     __typename
#   }
# }

# fragment PostVotesVotes on Post {
#   id
#   voteCount
#   votes(after: $after) {
#     items {
#       id
#       user {
#         ...DepreciatedUserLabelWithImageUser
#         __typename
#       }
#       __typename
#     }
#     pageInfo {
#       hasNextPage
#       nextCursor
#       __typename
#     }
#     __typename
#   }
#   __typename
# }

# fragment DepreciatedUserLabelWithImageUser on User {
#   id
#   image
#   ...DepreciatedUserLabelUser
#   __typename
# }

# fragment DepreciatedUserLabelUser on User {
#   id
#   image
#   username
#   url
#   karma
#   __typename
# }

class Queries:
	'There are all the graphql strings used'
	language_attributes = graphql.Field((
		'id',
		'displayName',
		'key',
		'category',
		'tagline',
		'icon',
		'isNew'
	))
	language_field = graphql.Field({
		'lang': language_attributes
	})
	languages_field = graphql.Field({
		'languages': language_attributes
	})

	user_attributes = graphql.Field((
		'id',
		'username',
		'url',
		'image',
		'firstName',
		'lastName',
		'fullName',
		'displayName',
		'isLoggedIn',
		'bio',
		'timeCreated',
		'isHacker',
		languages_field,
		graphql.Field({'roles': ('id', 'name', 'key', 'tagline')}),
	))
	user_field = graphql.Field({'user': user_attributes})
	repl_attributes = (
		'id',
		graphql.Alias(
			'embedUrl',
			graphql.Field('url', args={'lite': 'true'})
		),
		'hostedUrl',
		'title',
		language_field,
		'language',
		'timeCreated'
	)
	repl_field = graphql.Field({
		'repl': repl_attributes
	})
	board_field = graphql.Field({
		'board': (
			'id',
			'url',
			'slug',
			'cta',
			'titleCta',
			'bodyCta',
			'buttonCta',
			'description',
			'name',
			'replRequired',
			'isLocked',
			'isPrivate'
		)
	})

	def connection_generator(attributes):
		return graphql.Field({
			'pageInfo': (
				'hasNextPage',
				# 'hasPreviousPage',
				'nextCursor',
				# 'previousCursor'
			),
			'items': attributes
		})

	comment_attributes = graphql.Field((
		'id',
		'body',
		'voteCount',
		'timeCreated',
		'timeUpdated',
		user_field,
		'url',
		{'post': 'id'},
		{'parentComment': 'id'},
		{'comments': 'id'},
		'isAuthor',
		'canEdit',
		'canVote',
		'canComment',
		'hasVoted',
		'canReport',
		'hasReported',
		'isAnswer',
		'canSelectAsAnswer',
		'canUnselectAsAnswer',
		graphql.Field(
			'preview',
			args={
				'removeMarkdown': 'true',
				'length': 150
			}
		)
	))

	comment_connection_field = graphql.Field(
		'comments',
		args={
			'after': '$after',
			'count': '$count',
			'order': '$order'
		},
		data=connection_generator(comment_attributes)
	)

	post_vote_connection = graphql.Field(
		graphql.Field(
			'votes',
			args={
				'before': '$votesBefore',
				'after': '$votesAfter',
				'count': '$votesCount',
				'order': '$votesOrder',
				'direction': '$votesDirection'
			},
			data=connection_generator((
				'id',
				{'user': 'id'},
				{'post': 'id'}
			))
		)
	)

	post_attributes = graphql.Field((
		'id',
		'title',
		'body',
		'showHosted',
		'voteCount',
		'commentCount',
		'isPinned',
		'isLocked',
		'timeCreated',  # datetime
		'timeUpdated',  # datetime
		'url',
		user_field,  # User
		board_field,  # Board
		repl_field,  # Repl
		comment_connection_field,
		post_vote_connection,
		'isAnnouncement',
		'isAuthor',
		'canEdit',
		'canComment',
		'canVote',
		'canPin',
		'canSetType',
		'canChangeBoard',
		'canLock',
		'hasVoted',
		'canReport',
		'hasReported',
		'isAnswered',
		'isAnswerable',
		{'answeredBy': user_attributes},
		{'answer': comment_attributes},
		graphql.Field(
			'preview',
			args={
				'removeMarkdown': 'true',
				'length': 150
			}
		)

	))

	comment_connection_field = graphql.Field((
		connection_generator(comment_attributes)
	))

	comment_detail_comment_fragment = graphql.Fragment(
		'CommentDetailComment',
		'Comment',
		comment_attributes
	)
	get_post = graphql.Query(
		'post',
		{
			'$id': 'Int!',
			'$count': 'Int',
			'$order': 'String',
			'$after': 'String',
			'$votesBefore': 'String',
			'$votesAfter': 'String',
			'$votesCount': 'Int',
			'$votesOrder': 'String',
			'$votesDirection': 'String',
		},
		graphql.Field(
			args={'id': '$id'},
			data={
				'post': post_attributes
			}
		)
	)
	get_comment = graphql.Query(
		'comment',
		{
			'$id': 'Int!'
		},
		graphql.Field(
			args={'id': '$id'},
			data={
				'comment': comment_attributes
			}
		)
	)
	get_leaderboard = graphql.Query(
		'leaderboard', {'$after': 'String'},
		{
			graphql.Field(args={'after': '$after'}, data={
				'leaderboard': connection_generator(user_attributes)
			})
		}
	)
	
	delete_post = '''
	mutation deletePost($id: Int!) {
		deletePost(id: $id) {
			id
			__typename
		}
	}	
	'''
	
	delete_comment = '''
	mutation deleteComment($id: Int!) {
		deleteComment(id: $id) {
			id
			__typename
		}
	}
	'''
	
	# get_all_posts = f'''
	# query posts($order: String, $after: String, $searchQuery: String) {{
	# 	posts(order: $order, after: $after, searchQuery: $searchQuery) {{
	# 		pageInfo {{
	# 			nextCursor
	# 		}}
	# 		items {{
	# 			{post_field}
	# 		}}
	# 	}}
	# }}
	# '''
	posts_feed = graphql.Query(
		'ReplPostsFeed',
		{
			"$options": "ReplPostsQueryOptions",			
			'$count': 'Int',
			'$order': 'String',
			'$after': 'String',
			'$votesBefore': 'String',
			'$votesAfter': 'String',
			'$votesCount': 'Int',
			'$votesOrder': 'String',
			'$votesDirection': 'String',
		},
		graphql.Field(
			name='replPosts',
			args={
				'options': '$options'
			},
			data=connection_generator(post_attributes)
		)
	)
	get_comments = graphql.Query(
		'post',
		{'$id': 'Int!', '$commentsOrder': 'String', '$commentsAfter': 'String'},
		{
			graphql.Field('post', args={'id': '$id'}, data={
				graphql.Field(
					'comments',
					args={'order': '$commentsOrder', 'after': '$commentsAfter'},
					data={
						'pageInfo': 'nextCursor',
						'items': (
							comment_detail_comment_fragment,
							{
								'comments': comment_detail_comment_fragment
							}
						)
					}
				)
			})
		},
		fragments=[comment_detail_comment_fragment]
	)

	get_user = graphql.Query(
		'userByUsername',
		{'$username': 'String!'},
		graphql.Alias(
			'user',
			graphql.Field(
				{'userByUsername': user_attributes},
				args={'username': '$username'}
			)
		)
	)
	get_user_by_id = graphql.Query(
		'user',
		{'$user_id': 'Int!'},
		graphql.Alias(
			'user',
			graphql.Field(
				{'user': user_attributes},
				args={'id': '$user_id'}
			)
		)

	)

	# query: query userByUsername($username: String!, $pinnedReplsFirst: Boolean, $count: Int, $after: String, $before: String, $direction: String, $order: String) {
	#   user: userByUsername(username: $username) {
	#     id
	#     username
	#     firstName
	#     displayName
	#     isLoggedIn
	#     repls: publicRepls(pinnedReplsFirst: $pinnedReplsFirst, count: $count, after: $after, before: $before, direction: $direction, order: $order) {
	#       items {
	#         id
	#         timeCreated
	#         pinnedToProfile
	#         ...ProfileReplItemRepl
	#         __typename
	#       }
	#       pageInfo {
	#         hasNextPage
	#         nextCursor
	#       }
	#     }
	#   }
	# }



	get_user_repls = graphql.Query(
		'user',
		{
			'$user_id': 'Int!',
			'$pinnedFirst': 'Boolean',
			'$showUnnamed': 'Boolean',
			'$before': 'String',
			'$after': 'String',
			'$count': 'Int',
			'$order': 'String',
			'$direction': 'String'
		},
		graphql.Field('user', args={'id': '$user_id'},
		data={
			graphql.Field(
				'publicRepls', 
				args={
					'pinnedReplsFirst': '$pinnedFirst',
					'showUnnamed': '$showUnnamed',
					'before': '$before',
					'after': '$after',
					'count': '$count',
					'order': '$order',
					'direction': '$direction'
				},
				data={
					'pageInfo': (
						'nextCursor',
						'hasNextPage'
					),
					'items': (
						repl_attributes
					)
				}
			)
		})
	)

# query ProfileComments($username: String!, $after: String, $order: String) {
#   user: userByUsername(username: $username) {
#     id
#     displayName
#     comments(after: $after, order: $order) {
#       items {
#         id
#         ...ProfileCommentsComment
#         __typename
#       }
#       pageInfo {
#         nextCursor
#         __typename
#       }
#       __typename
#     }
#     __typename
#   }
# }

	get_user_comments = graphql.Query(
		'ProfileComments',
		{'$user_id': 'Int!', '$order': 'String', '$after': 'String', '$count': 'Int'},
		graphql.Field(
			'user',
			args={'id': '$user_id'},
			data={
				graphql.Field(
					'comments',
					args={'order': '$order', 'after': '$after', 'count': '$count'},
					data=connection_generator(comment_attributes)
				)
			}
		)
	)

	get_user_posts = graphql.Query(
		'user',
		{
			'$user_id': 'Int!',
			'$order': 'String',
			'$after': 'String',
			'$count': 'Int',
			'$votesBefore': 'String',
			'$votesAfter': 'String',
			'$votesCount': 'Int',
			'$votesOrder': 'String',
			'$votesDirection': 'String'
		},
		graphql.Field(
			'user',
			args={'id': '$user_id'},
			data={
				graphql.Field(
					'posts',
					args={
						'order': '$order',
						'after': '$after',
						'count': '$count'
					},
					data={
						'pageInfo': 'nextCursor',
						'items': (
							post_attributes
						)
					}
				)
			}
		)
	)
	
	ban_user = '''
	mutation Mutation($user: String!, $reason: String) {
		clui {
			moderator {
				user {
					ban(user: $user, reason: $reason) {
						...CluiOutput
						__typename
					}
					__typename
				}
				__typename
			}
			__typename
		}
	}
	
	fragment CluiOutput on CluiOutput {
		... on CluiSuccessOutput {
			message
			json
			__typename
		}
		... on CluiErrorOutput {
			error
			json
			__typename
		}
		... on CluiMarkdownOutput {
			markdown
			__typename
		}
		... on CluiTableOutput {
			columns {
				label
				key
				__typename
			}
			rows
			__typename
		}
		__typename
	}
	'''
		
	
	report_attributes = graphql.Field(
		{'creator': user_attributes},
		'id',
		'reason',
		'resolved',
		'timeCreated',
		'type',
		{'post': graphql.Field('url', 'body', 'id', {'user': user_attributes}, 'title')},
		{'comment': graphql.Field(
			'url',
			'body',
			{'post': 'id'},
			{'user': user_attributes},
			'id'
		)}
	)
	resolve_report = graphql.Mutation(
		'resolveBoardReport',
		{
			'$id': 'Int!'
		},
		graphql.Field(
			'resolveBoardReport',
			args={'id': '$id'},
			data=report_attributes
		)
	)
	get_reports = graphql.Query(
		'boardReports',
		{
			'$unresolvedOnly': 'Boolean!'
		},

		graphql.Field(
			'boardReports',
			args={'unresolvedOnly': '$unresolvedOnly'},
			data=report_attributes
		)
	)
	get_lazy_reports = graphql.Query(
		'boardReports',
		{
			'$unresolvedOnly': 'Boolean!'
		},

		graphql.Field(
			'boardReports',
			args={'unresolvedOnly': '$unresolvedOnly'},
			data=graphql.Field(
				'id',
				'reason',
				{'creator': user_attributes}
			)
		)
	)
	# get_comments = f'''
	# query post(
	# 	$id: Int!, $commentsOrder: String, $commentsAfter: String
	# ) {{
	# 	post(id: $id) {{
	# 		comments(order: $commentsOrder, after: $commentsAfter) {{
	# 			pageInfo {{
	# 				nextCursor
	# 			}}
	# 			items {{
	# 				...CommentDetailComment
	# 				comments {{
	# 					...CommentDetailComment
	# 				}}
	# 			}}
	# 		}}
	# 	}}
	# }}

	# fragment CommentDetailComment on Comment {{
	# 	id
	# 	body
	# 	timeCreated
	# 	canEdit
	# 	canComment
	# 	canReport
	# 	hasReported
	# 	url
	# 	voteCount
	# 	canVote
	# 	hasVoted
	# 	{user_field}
	# }}

	# '''
	# query comments($after: String, $order: String) {
	# 	comments(after: $after, order: $order) {
	# 		items {
	# 			id
	# 		}
	# 	}
	# }
	get_all_comments = '''
	query comments($after: String, $order: String) {{
		comments(after: $after, order: $order) {{
			items {{
				id
				body
				user {
					username
					id
				}
				comments {{
					id
					body
					user {
						username
						id
					}
				}}
			}}
			pageInfo {{
				hasNextPage
				nextCursor
			}}
		}}
	}}
	'''
	
	post_exists = graphql.Query('post', {'$id': 'Int!'}, {
		graphql.Field('post', args={'id': '$id'}, data='id')
	})


# query ProfilePosts($username: String!, $after: String, $order: String, $count: Int) {  user: userByUsername(username: $username) {    id    displayName    posts(after: $after, order: $order, count: $count) {      items {        id        ...PostsFeedItemPost        board {          id          name          url          slug          color          __typename        }        __typename      }      pageInfo {        nextCursor        __typename      }      __typename    }    __typename  }}fragment PostsFeedItemPost on Post {  id  title  preview(removeMarkdown: true, length: 150)  url  commentCount  isPinned  isLocked  isAnnouncement  timeCreated  isAnswered  isAnswerable  ...PostVoteControlPost  ...PostLinkPost  user {    id    username    isHacker    image    isModerator: hasRole(role: MODERATOR)    isAdmin: hasRole(role: ADMIN)    ...UserLabelUser    ...UserLinkUser    __typename  }  repl {    id    lang {      id      icon      key      displayName      tagline      __typename    }    __typename  }  board {    id    name    slug    url    color    __typename  }  recentComments(count: 3) {    id    ...SimpleCommentComment    __typename  }  __typename}fragment PostVoteControlPost on Post {  id  voteCount  canVote  hasVoted  __typename}fragment PostLinkPost on Post {  id  url  __typename}fragment UserLabelUser on User {  id  username  karma  ...UserLinkUser  __typename}fragment UserLinkUser on User {  id  url  username  __typename}fragment SimpleCommentComment on Comment {  id  user {    id    isModerator: hasRole(role: MODERATOR)    isAdmin: hasRole(role: ADMIN)    ...UserLabelUser    ...UserLinkUser    __typename  }  preview(removeMarkdown: true, length: 500)  timeCreated  __typename}
	profile_posts = graphql.Query('ProfilePosts', {
		'$username': 'String!',
		'$after': 'String',
		'$order': 'String',
		'$count': 'Int',
	}, {
	})
	create_report = graphql.Mutation(
		'createBoardReport',
		{
			'$postId': 'Int',
			'$commentId': 'Int',
			'$reason': 'String!'
		},
		graphql.Field(
			{
				'createBoardReport':
				(
					'id',
				)
			},
			args={
				'postId': '$postId',
				'commentId': '$commentId',
				'reason': '$reason' 
			},
		)
	)
	# create_report_2 = '''
	# mutation createBoardReport() {
	# 	createBoardReport(postId: $postId, $commentId: Int, $reason: string!) {
	# 		id
	# 	}
	# }
	# '''
	create_post = '''
	mutation createPost($input: CreatePostInput!) {
		createPost(input: $input) {
			post {
				id
				url
				showHosted
				board {
					id
					name
					slug
					url
					replRequired
					template
				}
			}
		}
	}
	'''

	create_comment = '''
	mutation createComment($input: CreateCommentInput!)
		{ createComment(input: $input)
			{ 
				comment 
				{ id ...CommentDetailComment comments
					{ id ...CommentDetailComment __typename } 
					parentComment { id __typename } __typename
				} __typename 
			} 
		} 
		fragment CommentDetailComment on Comment {
			id
			body
			timeCreated
			canEdit
			canComment
			canReport
			hasReported
			url
			canSelectAsAnswer
			canUnselectAsAnswer
			isAnswer 
			...CommentVoteControlComment
			user {
				id
				username
				...DepreciatedUserLabelWithImageUser
				__typename 
			}
			post { id isAnswerable __typename } 
			...EditCommentComment __typename 
		}
		fragment DepreciatedUserLabelWithImageUser on User {
			id
			image
			...DepreciatedUserLabelUser
			__typename 
		} 
		fragment DepreciatedUserLabelUser on User {
			id
			image
			username
			url
			karma __typename
		}
		fragment CommentVoteControlComment on Comment {
			id
			voteCount
			canVote
			hasVoted
			__typename
		}
		fragment EditCommentComment on Comment {
			id
			parentComment
			{ id __typename }
			post { id __typename }
			__typename }
		'''
