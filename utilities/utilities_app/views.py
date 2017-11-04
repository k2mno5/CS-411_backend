# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponse
from django.shortcuts import render
from models import Questions
from . import management
import time
import logging


# Logger in view module
stdlogger = logging.getLogger(__name__)

# testing functions uncomment to test
def index(request):
    stdlogger.info("Entering index method")
    return HttpResponse("index method in views")

def showUID(request, userID):
    time_s = time.time()
    data = Questions.objects.all()
    res = data[len(data)-1]
    time_e = time.time()
    return HttpResponse("{}\n {} \n{}".format((time_e-time_s),res, userID))

def showQID(request):
    return management.data_process_showQID(request)

# ================= Functions and APIs ====================

# updateVoteStatus
# input: Http get_request
# output: empty http response
def updateVoteStatus(request, postID, postType, userID, voteStatus):
    postID = int(postID)
    postType = int(postType)
    userID = int(userID)
    voteStatus = int(voteStatus)
    return management.updateVoteStatus(postID, postType, userID, voteStatus)
