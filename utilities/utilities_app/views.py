# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import *
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from models import Questions
from . import management
import time
import logging
from django.http import JsonResponse
import json
from django.core import serializers



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
#       ques, specify whether a question an all of its answers will return
# output json file specified online
def displayQuestionAnswers(request, qaID, is_ques):
    return management.displayQuestionAnswers(int(qaID), int(is_ques))


# post answer, add an answer to the question
# input request containing the json file of hte answer
# output ack
# side-effect: answer piped into the database
@csrf_exempt
def postAnswer(request):
    return management.postAnswer(request.body)

@csrf_exempt
def postQuestion(request):
    return management.postQuestion(request.body)

# delete a post, could be a question or an answer
def deletePost(request, ID, is_ques):
    return management.deletePost(int(ID), int(is_ques))


# get following status by Luo
@csrf_exempt
def getFollowingStatus(request):
    jsonBody = json.loads(request.body)

    # check if missing fields
    if 'content' not in jsonBody or 'userID' not in jsonBody['content'] or 'target' not in jsonBody['content']:
        return HttpResponseBadRequest('Missing field')

    # check if field type match
    uID = -1
    try:
        uID = int(jsonBody['content']['userID'])
    except:
        return HttpResponseBadRequest('Field type does not match')

    targets = []
    for target in jsonBody['content']['target']:
        try:
            targets.append(int(target))
        except:
            return HttpResponseBadRequest('Field type does not match')

    res = management.getFollowingStatus(uID, targets)
    res_dict = {}
    res_dict['following_results'] = []
    for status in res:
        if status == 0:
            res_dict['following_results'].append("n")
        else:
            res_dict['following_results'].append("y")
    return JsonResponse(res_dict)

# get vote status by luo
@csrf_exempt
def getVoteStatus(request):
    jsonBody = json.loads(request.body)

    # check if missing fields
    if 'content' not in jsonBody or 'userID' not in jsonBody['content'] or 'qIDs' not in jsonBody['content'] or 'aIDs' not in jsonBody['content']:
        return HttpResponseBadRequest('Missing field')

    # check if field type match
    uID = -1
    try:
        uID = int(jsonBody['content']['userID'])
    except:
        return HttpResponseBadRequest('Field type does not match')

    qIDs = []
    aIDs = []
    for target in jsonBody['content']['qIDs']:
        try:
            qIDs.append(int(target))
        except:
            return HttpResponseBadRequest('Field type does not match')

    for target in jsonBody['content']['aIDs']:
        try:
            aIDs.append(int(target))
        except:
            return HttpResponseBadRequest('Field type does not match')


    qRes, aRes = management.getVoteStatus(uID, qIDs, aIDs)
    res_dict = {}
    res_dict['question_voted_status'] = []
    res_dict['answer_voted_status'] = []
    for status in qRes:
        res_dict['question_voted_status'].append(status)
    for status in aRes:
        res_dict['answer_voted_status'].append(status)
    return JsonResponse(res_dict)

def getFollowingActivities(request, userID, page):
    uID = -1
    pageOffset = -1
    try:
        uID = int(userID)
        pageOffset = int(page)
    except:
        return HttpResponseBadRequest('Field type does not match')

    if pageOffset < 0:
        return HttpResponseBadRequest('Invalid page offset')

    res = management.getFollowingActivities(uID, pageOffset)

    if res is None:
        return HttpResponseBadRequest('Invalid User ID')
    else:
        res['page'] = pageOffset
        return JsonResponse(res)

def getUserStatus(request, userID, showActivities):
    uID = -1
    showAct = True
    try:
        uID = int(userID)
        if int(showActivities) == 0:
            showAct = False
    except:
        return HttpResponseBadRequest('Field type does not match')

    res = management.getUserStatus(userID, showAct)

    if res is None:
        return HttpResponseBadRequest('Invalid User ID')
    else:
        return JsonResponse(res)

def getFollows(request, requestType, userID, page, showDetail):
    try:
        uID = int(userID)
        pageOffset = int(page)
        returnDetail = True
        if showDetail == "0":
            returnDetail = False

        res = management.getFollows(uID, pageOffset, (requestType == "followings"), returnDetail)
        res['page'] = pageOffset
        return JsonResponse(res)
    except:
        # this should never happend since regex makes sure that parameters can be parsed to corresponding type
        return HttpResponseBadRequest('Field type does not match')


def getCertainActivities(request, userID, postType, actionType, page):
    try:
        uID = int(userID)
        post = int(postType)
        action = int(actionType)
        pageOffset = int(page)
        res = management.getCertainActivities(uID, post, action, pageOffset)
        res['page'] = pageOffset
        return JsonResponse(res)

    except:
        return HttpResponseBadRequest('Field type does not match')

# update followers function, expecting a JSON input
@csrf_exempt
def updateFollowers(request):
    return management.updateFollowers(request.body)

@csrf_exempt
def updateUserInfo(request):
    return management.updateUserInfo(request.body)