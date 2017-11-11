# system dependency
from __future__ import unicode_literals
import logging
import time
import django.db.models
from django.http import HttpResponse

# datebase dependency
from . import models as StackQuora
from django.db.models import Max
from random import randint
from django.core.exceptions import ObjectDoesNotExist

# date processing dependency
from django.core import serializers
from . import json_parser
from django.http import JsonResponse
import time
import datetime
import json

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

	return HttpResponse("Success!")

# getUserUpdate
# input: uID
# output: short version question JSON specified on stackoverflow issue
# side-effect: none
# description: first stage will only randomly return ten questions
#  			    will return actual questions that is related later on.
def getUserUpdate_random():
	random_data_questions = StackQuora.Questions
	random_data = []
	random_tags = StackQuora.Tags
	question_ID = []
	tag_array = []
	max_ = random_data_questions.objects.aggregate(Max('qid'))['qid__max']
	i = 0
	while i < 10:
		try:
			random_data.append(random_data_questions.objects.get(pk = randint(1, max_)))
			i += 1
		except ObjectDoesNotExist:
			pass
	for e in random_data:
 		question_ID.append(e.qid)
	
	# get data from Tags table for each question retrived, one time evaluation
	for e in random_tags.objects.filter(tid__in = question_ID):
		tag_array.append((e.tags, e.tid))

 	# formatting json object	
 	data_json = serializers.serialize('json', random_data)
 	data_json = json_parser.json_getUserUpdate(data_json, tag_array, len(tag_array))
	return JsonResponse(data_json)


# display question answers
# input ID, possibly UID or AID, 
#		ques, specify whether a question an all of its answers will return
# output json file specified online
# lets try 38817270 as qid first
# owner id 4576857
# creation date "2016-08-07T18:32:13Z"
# closed date NULL
# title "Java Application to Access PC wifi direct OR Java - Wifi API",
''' tags     "android",
    "java",
    "wifi-direct",
    "wifip2p"
'''
def displayQuestionAnswers(qaID, is_ques):
	data_json = {}
	questionAuther = ()
	aAuthorID = []
	answerAuthors = []
	if is_ques != 0:
		# try to get questions specified by qaID
		try:
			req_question = StackQuora.Questions.objects.get(qid = qaID)
		except ObjectDoesNotExist:
			return HttpResponse("qID no longer exist in the database")

		# try to get corresponding answers may be empty
		req_answers = StackQuora.Answers.objects.filter(parentid = req_question.qid)
		
		# try to get three tags
		tags = StackQuora.Tags.objects.filter(tid = req_question.qid)
		tag_array = []
		i = 0
		for instance in tags:
			tag_array.append(instance.tags)
			i+=1
			if i == 3:
				break

		# try to get corresonding question owner
		questionAuthor = StackQuora.Users.objects.get(uid = req_question.owneruserid)
		questionAuthor = (questionAuthor.username, questionAuthor.reputation, questionAuthor.uid)

		# try to get corresponding answer owner if there is any answser
		# with ingle database evaluation
		for instance in req_answers:
			aAuthorID.append(instance.owneruserid)
		answerAuthors_object = StackQuora.Users.objects.filter(uid__in = aAuthorID)
		for instance in req_answers:
			for user in answerAuthors_object:
				if user.uid == instance.owneruserid:
					answerAuthors.append((user.username,user.reputation,user.uid))

		data_json =  json_parser.json_displayQuestionAnswers(req_question, 
			req_answers,tag_array, questionAuthor, answerAuthors)

	else:
		try:
			req_answer = StackQuora.Answers.objects.get(aid  = qaID)
		except ObjectDoesNotExist:
			return HttpResponse("aID no longer exist in the database")
		answerAuthor = StackQuora.Users.objects.get(uid = req_answer.owneruserid)
		answerAuthors.append((answerAuthor.username,answerAuthor.reputation, answerAuthor.uid))
		data_json = json_parser.json_displayQuestionAnswers(None, 
			[req_answer], [], ("",0), answerAuthors)
	return JsonResponse(data_json)


# delete a post, could either be an answer or a question
# input: ID, qid or aid, is_ques specify whether this is 
#	an answer or not
# side effect: delete corresponding database entry
def deletePost(ID, is_ques):
	# if deleting a question, all other things has to be deleted
	if is_ques:
		stdlogger.info("is question")
		has_answer = True
		has_tag = True
		try:
			question = StackQuora.Questions.objects.get(qid = ID)
		except ObjectDoesNotExist:
			return HttpResponse("qID no longer exist in the database.")
		
		try:
			answers = StackQuora.Answers.objects.filter(parentid = question.qid)
		except ObjectDoesNotExist:
			has_answer = False
		
		try:
			tags = StackQuora.Tags.objects.filter(tid = question.qid)
		except ObjectDoesNotExist:
			has_tag = False

		if has_answer:
			answers.delete()

		if has_tag:
			tags.delete()

		question.delete()

	# else if we are deleting answer
	else:
		stdlogger.info("is answer only")
		try:
			answer = StackQuora.Answers.objects.get(aid = ID)
		except ObjectDoesNotExist:
			return HttpResponse("aID no longer exist in the database.") 
		answer.delete()
	return HttpResponse("Successfully deleted!")


# post Answer, used to post answer to a question
# input http post request body
# side effect insert answer into the database
def postAnswer(body):
	inJson = json.loads(body)
	answer_content = inJson['content']

	try:
		StackQuora.Users.objects.get(uid = int(answer_content['userID']))
	except ObjectDoesNotExist:
		return HttpResponse("No corresponding user exists: {}".format(int(answer_content['userID'])))
	
	try:
		StackQuora.Questions.objects.get(qid = int(answer_content['parentID']))
	except ObjectDoesNotExist:
		return HttpResponse("No corresponding question exists.")

	max_ = StackQuora.Answers.objects.aggregate(Max('aid'))['aid__max']
	aID = max_ + 1
	owneruserID = int(answer_content['userID'])
	body = (answer_content['body'])
	parentID = int(answer_content['parentID'])
	score = 0
	upVote = 0
	downVote = 0
	private = 0
	creationDate = datetime.datetime.utcnow()

	try:
		new_answer = StackQuora.Answers.objects.create(aid = aID, 
			owneruserid = owneruserID, body = body, parentid = parentID
			, score = score, upvote = upVote, downvote = downVote, 
			private = private, creationdate = creationDate)
	except IntegrityError:
		return HttpResponse("IntegrityError occured, check your pkey.")

	return HttpResponse("Answer added.")



