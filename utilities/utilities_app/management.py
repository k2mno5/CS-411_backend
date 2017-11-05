# system dependency
from __future__ import unicode_literals
import logging
import time
from django.http import HttpResponse

# datebase dependency
from . import models as StackQuora

# logger for management module
stdlogger = logging.getLogger(__name__)

# testing function uncomment to use
def data_process_showQID(request):
    stdlogger.info(request)
    return HttpResponse("This link shows Questions")

# ================= Functions and APIs ====================

# updateVoteStatus
# input: post ID, 
#        post Type (0: question, 1: answers), 
#        userID, 
#        voteStatus (0: down vote, 1: reset, 2: upvote)
# output: empty http response
# sample url: localhost/utilities/post/vote/999/0/9999/1/
def updateVoteStatus(postID, postType, userID, voteStatus):
	if postType == 0:
		data = StackQuora.Questions.objects.filter(qid = postID)
	else:
		data = StackQuora.Answers.objects.filter(aid = postID)

	if not data:
		raise Exception("Something is wrong, postID not found, unable to update.")

	if voteStatus == 0:
		data.downvote += 1
	elif voteStatus == 1:
		data.upvote +=1
	else:
		data.downvote = 0
		data.upvote = 0
	data.save(['downvote', 'upvote'])
	return HttpResponse()

# getUserUpdate
# input: post ID, 
#        post Type (0: question, 1: answers), 
#        userID, 
#        voteStatus (0: down vote, 1: reset, 2: upvote)
# output: empty http response
# sample url: localhost/utilities/post/vote/999/0/9999/1/

