# system dependency
from __future__ import unicode_literals
import logging
import time
from django.http import HttpResponse

# datebase dependency
from . import models as StackQuora

# date processing dependency
from django.core import serializers
from . import json_parser

# logger for management module
stdlogger = logging.getLogger(__name__)

# ================= Functions and APIs ====================

# updateVoteStatus
# input: post ID, 
#        post Type (0: question, 1: answers), 
#        userID, 
#        voteStatus (0: down vote, 1: reset, 2: upvote)
# output: empty http response
# side-effect: updating table
# sample url: localhost/utilities/post/vote/999/0/9999/1/
def updateVoteStatus(postID, postType, userID, voteStatus):
	time_s = time.time()
	try:
		if postType == 0:
			data = StackQuora.Questions.objects.get(qid = postID)
		else:
			data = StackQuora.Answers.objects.get(aid = postID)
	except:
		return HttpResponse("No corresponding Questions/Answers \
			found in table, something is wrong, \
			check your record.")

	if voteStatus == 0:
		data.downvote += 1
	elif voteStatus == 1:
		data.upvote +=1
	else:
		data.downvote = 0
		data.upvote = 0

	# update database
	data.save()

	# update recommandation system

	time_e = time.time()
	return HttpResponse("{}".format(time_e - time_s))

# getUserUpdate
# input: uID
# output: short version question JSON specified on stackoverflow issue
# side-effect: none
# description: first stage will only randomly return ten questions
#  			    will return actual questions that is related later on.
def getUserUpdate_random():
	random_data = StackQuora.Questions
	random_tags = StackQuora.Tags
	question_ID = []
	tag_array = []

	# get data from Questions table
	random_data = random_data.objects.raw("SELECT * FROM Questions WHERE RAND() LIMIT 10;")
 	
 	for e in random_data:
 		question_ID.append(e.qid)

 	# get data from Tags table for each question retrived
 	for ID in question_ID:
 		tag_array.append(random_tags.objects.raw("SELECT * FROM Tags WHERE tID = %s", [ID]))

 	data_json = serializers.serialize('json', random_data)
 	data_json = json_parser.json_getUserUpdate(data_json, tag_array, len(tag_array))

 	return HttpResponse(data_json, content_type = "appn/json")

