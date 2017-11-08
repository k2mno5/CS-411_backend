from __future__ import unicode_literals
import json
import collections
import logging
import time



# logger for management module
stdlogger = logging.getLogger(__name__)

# ================= Functions and APIs ====================

# json parser for getUserUpdate function in management.py
# input JSONInFile: String, tagArray: RawQuerySet, numData: integer
# output parsed json file according to spec
# description: given a complex structure query json file, 
#	output a simple serialized json file suits our model
# sideeffects: none
def json_getUserUpdate(JSONInFile, tagArray, numData):
	JSONOutFile = []
	t0 = time.time()
	JSONInFile = json.loads(JSONInFile)
	for instance in JSONInFile:
		json_dic = collections.OrderedDict()
		json_dic['qID'] = instance['pk']
		json_dic['owneruserid'] = instance['fields']['owneruserid']
		json_dic['creationdate'] = instance['fields']['creationdate']
		json_dic['closeddate'] = instance['fields']['closeddate']
		json_dic['title'] = instance['fields']['title']
		json_dic['body'] = instance['fields']['body']
		json_dic['score'] = instance['fields']['score']
		json_dic['upvote'] = instance['fields']['upvote']
		json_dic['downvote'] = instance['fields']['downvote']
		json_dic['private'] = instance['fields']['private']
		JSONOutFile.append(json_dic)

	for instance in JSONOutFile:
		instance['tags'] = []
		for each_tag in tagArray:
			if instance['qID'] == each_tag[1]:
				instance['tags'].append(each_tag[0])
	

	JSONOutDict = {}
	JSONOutDict['contents'] = JSONOutFile 
	# return json.dumps(JSONOutDict)
	return JSONOutDict
	

# json parser for displayQuestionAnswers function in management.py
# input dataframe file: req_question, req_answers
# output parsed json file according to spec
def json_displayQuestionAnswers(req_question, req_answers, tagArray, questionAuthor, answerAuthors):
	JSONOutDict = {}
	if req_question is not None:
		questionDict = collections.OrderedDict()
		questionDict['qid']  =req_question.qid
		questionDict['authorName'] = questionAuthor[0]
		questionDict['reputation'] = questionAuthor[1]
		questionDict['title'] = req_question.title
		questionDict['body'] = req_question.body
		questionDict['upvote'] = req_question.upvote
		questionDict['downvote']  =req_question.downvote
		# number of comment omit for now
		# vote status omit for now
		questionDict['posted_time'] = req_question.creationdate
		questionDict['closed_time'] = req_question.closeddate
		questionDict['tags'] = tagArray
		# following omit for now but will add in later or rather it is not a good idea
		# to place if a user is following an author in this json file.
		JSONOutDict['question'] = questionDict

	stdlogger.info(answerAuthors)
	stdlogger.info(req_answers)

	if req_answers:
		answers = []
		i = 0
		for instance in req_answers:
			answerDict = collections.OrderedDict()
			answerDict['aid'] = instance.aid
			answerDict['authorName'] = answerAuthors[i][0]
			answerDict['reputation'] = answerAuthors[i][1]
			answerDict['body'] = instance.body
			answerDict['upvote'] = instance.upvote
			answerDict['downvote'] = instance.downvote
			# vote status omit for now, since we have update vote
			answerDict['creationdate'] = instance.creationdate
			# for the same reason, omit following
			i+=1
			answers.append(answerDict)
		JSONOutDict['answers'] = answers
	return JSONOutDict