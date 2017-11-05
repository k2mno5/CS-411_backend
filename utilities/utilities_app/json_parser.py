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
		instance['tag'] = []
		for each_tag in tagArray:
			if instance['qID'] == each_tag[1]:
				instance['tag'].append(each_tag[0])
	

	JSONOutDict = {}
	JSONOutDict['contents'] = JSONOutFile 
	return json.dumps(JSONOutDict)

	
