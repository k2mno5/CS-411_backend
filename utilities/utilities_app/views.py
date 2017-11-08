# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponse
from django.shortcuts import render
from models import Questions
from . import management
import time
import logging

# Logger in view module see README to use the logger print here will not work
stdlogger = logging.getLogger(__name__)


# Default view
def index(request):
    return HttpResponse("If you see this page, Apache httpd and django is running.")


# ================= Functions and APIs ====================

# updateVoteStatus wrapper
# input: Http get_request
# output: empty http response
def updateVoteStatus(request, postID, postType, userID, voteStatus):
    postID = int(postID)
    postType = int(postType)
    userID = int(userID)
    voteStatus = int(voteStatus)
    return management.updateVoteStatus(postID, postType, userID, voteStatus)

# getUserUpdate wrapper
# input uID, Http_get_request
# output: JSON file, schema on github issue
# @NOTE, in this version, 10 random questions will be return
#        to return preference related questions, change the
#        getUserUpdate_random to getUserUpdate, which will be
#        implemented later on.
def getUserUpdate_random(request):
    return management.getUserUpdate_random()

# display question answers
# input ID, possibly UID or AID, 
#		ques, specify whether a question an all of its answers will return
# output json file specified online
def displayQuestionAnswers(request, qaID, is_ques):
	return management.displayQuestionAnswers(int(qaID), int(is_ques))