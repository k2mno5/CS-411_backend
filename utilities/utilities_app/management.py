# system dependency
from __future__ import unicode_literals
import logging
import time
import django.db.models
from django.http import HttpResponse
from django.http import *


# datebase dependency
from . import models as StackQuora
from django.db.models import Max
from random import randint
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
 

# date processing dependency
from django.core import serializers
from django.http import JsonResponse
from . import json_parser
import time
import datetime
import json

# logger for management module
stdlogger = logging.getLogger(__name__)

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# ================= Functions and APIs ====================

# getFollowingStatus
#   Function to check if one user is following other users specified in targets
# param:    uID : an integer of the user to check its following status
#       targets : a list of integer contains uIDs for checking if they are followed
# return:   res : a list of 0 or 1 indicating if the target is being followed (0: no; 1: yes)
# note:
#   If the userID is invalid (not in the database), res will be a list of all 0s
#   If an userID in targets is invalid, corresponding slot in res will be 0

def getFollowingStatus(uID, targets):
    # prepare WHERE clause
    where = " WHERE uid = {} and (".format(uID)
    for targetID in targets:
        where += " uidfollowing = {} or ".format(targetID)
    where += " true = false)" # "true = false" to handle the tailing or

    # raw SQL query
    query = "SELECT * FROM Following" + where

    status = StackQuora.Following.objects.raw(query)

    res = []
    for targetID in targets:
        if any(tup.uidfollowing == targetID for tup in status):
            res.append(1)
        else:
            res.append(0)
    return res

def getVoteStatus(uID, qIDs, aIDs):
    # prepare WHERE clause
    where = " WHERE uid = {} and (".format(uID)
    for qID in qIDs:
        where += " (actionid = {} and (actiontype = {} or actiontype = {})) or ".format(qID, 2, 4)
    for aID in aIDs:
        where += " (actionid = {} and (actiontype = {} or actiontype = {})) or ".format(aID, 3, 5)
    where += " true = false)" # "true = false" to handle the tailing or

    # raw SQL query
    query = "SELECT * FROM ActivityHistory" + where

    status = StackQuora.Activityhistory.objects.raw(query)

    qRes = []
    aRes = []
    for qID in qIDs:
        found = False
        for res in status:
            if res.actionid == qID:
                if res.actiontype == 2 or res.actiontype == 4:
                    found = True
                    if res.actiontype == 2:
                        qRes.append(1)
                    else:
                        qRes.append(-1)
                    break
        if not found:
            qRes.append(0)

    for aID in aIDs:
        found = False
        for res in status:
            if res.actionid == aID:
                if res.actiontype == 3 or res.actiontype == 5:
                    found = True
                    if res.actiontype == 3:
                        aRes.append(1)
                    else:
                        aRes.append(-1)
                    break
        if not found:
            aRes.append(0)


    return qRes, aRes

# getUserActivities
# params: uIDs, a list of user IDs to get activities from
#         numOfPost, int of the number of post (activities) to be shown
#         pageOffset, int of page offset for skipping first (pageOffset * numOfPost) posts
#         showActionType, int of a 3-bit indicator (0b111, 1st: show downvote; 2nd: shown upvote; 3rd: show post)
#         showPostType, int of a 2-bit indicator (0b11, 1st: show answers; 2nd: show questions)
# return: an activities dict
#             keys: 'uIDs', a list of uIDs for activity initiator of activities in corresponding index
#                   'recentActivities', a list of activity dict for each activity
#                       keys: 'postID', 'postType', 'actionType', 'time'
def getUserActivities(uIDs, numOfPost=10, pageOffset=0, showActionType=7, showPostType = 3):
    # POST_MASK = 1; UPVOTE_MASK = 2; DOWNVOTE_MASK = 4
    typeMask = [1, 2, 4]

    # QUESTION_MASK = 1; ANSWER_MASK = 2
    postMask = [1, 2]

    actionInclude = []
    postInclude = []
    for i in range(len(typeMask)):
        if showActionType & typeMask[i] != 0:
            actionInclude.append(i)
    for i in range(len(postMask)):
        if showPostType & postMask[i] != 0:
            postInclude.append(i)

    # generate the range of action types that the return should include
    actionRange = []
    for i in actionInclude:
        for j in postInclude:
            actionRange.append( i * len(postMask) + j )

    activities = StackQuora.Activityhistory.objects.filter(uid__in = uIDs, actiontype__in = actionRange).order_by('-time')[pageOffset*numOfPost:(pageOffset+1)*numOfPost]

    res = {"uIDs":[], "recentActivities":[]}
    for activity in activities:
        res["uIDs"].append(activity.uid)
        res["recentActivities"].append({"postID":activity.actionid, "postType":activity.actiontype%2, "actionType":activity.actiontype/2, "time":activity.time.strftime(TIME_FORMAT)})

    return res

def getUserStatus(uID, showActivities):
    userStatus = None
    try:
        userStatus = StackQuora.Users.objects.get(uid = uID)
    except ObjectDoesNotExist:
        return None


    res = {"userName":userStatus.username, "following":userStatus.following, "follower":userStatus.follower, "reputation":userStatus.reputation, "lastLogin": userStatus.lastlogin.strftime(TIME_FORMAT)}

    if showActivities:
        userActivities = getUserActivities([uID])
        res["recentActivities"] = userActivities["recentActivities"]

        # get post detail
        postIDs = []
        postTypes = []
        for activity in res['recentActivities']:
            postIDs.append(activity["postID"])
            postTypes.append(activity["postType"])

        res["postDetail"] = getPosts(postIDs, postTypes)

    return res
        
def getFollowingActivities(uID, page):
    try:
        StackQuora.Users.objects.get(uid = uID)
    except ObjectDoesNotExist:
        return None

    following = StackQuora.Following.objects.filter(uid = uID)
    followingUIDs = []
    for relation in following:
        followingUIDs.append(relation.uidfollowing)

    res = getUserActivities(followingUIDs, pageOffset = page, showActionType = (1<<0 | 1<<1))

    # get post detail
    postIDs = []
    postTypes = []
    for activity in res['recentActivities']:
        postIDs.append(activity["postID"])
        postTypes.append(activity["postType"])

    res["postDetail"] = getPosts(postIDs, postTypes)
    return res
    return res


def getFollows(uID, pageOffset, following, showDetail, numOfUsers = 20):
    uIDs = []
    follows = None
    if following:
        follows = StackQuora.Following.objects.filter(uid = uID).order_by('uidfollowing')[pageOffset*numOfUsers:(pageOffset+1)*numOfUsers]
    else:
        follows = StackQuora.Following.objects.filter(uidfollowing = uID).order_by('uid')[pageOffset*numOfUsers:(pageOffset+1)*numOfUsers]

    for follow in follows:
        if follow.uid == uID:
            uIDs.append(follow.uidfollowing)
        else:
            uIDs.append(follow.uid)

    res = {'uIDs': uIDs}
    if showDetail:
        res['userStatus'] = []
        for ID in uIDs:
            detail = getUserStatus(ID, False)
            res['userStatus'].append(detail)
    return res

# reinventing the wheel here. If displayQuestionAnswers can be separated into a function for returning http response and the other function for returning gathered data would be helpful
# this is helper function, thus assuming the len of postIDs and postTypes are the same and they are valid values
# getPosts
# params: postIDs, a list of post ID (each post can be either question or answer)
#         postTypes, a list of post type (0: question; 1: answer)
# return: res, a list of postDetail dict
#             keys of postDetail are: 'postID', 'userID', 'title', 'body', 'upVotes', 'downVotes', 'creationDate'
#                 Notice that 'title' of an answer will be the title of its parent (question)
def getPosts(postIDs, postTypes):
    # assign to postTypes just for place holding
    res = postTypes
    
    answerList = []
    questionList = []

    # filter out answers and questions because for each answers, we would also need to get its parent
    # Thus we will get all answers first, and append their parents' IDs to questionList to reduce number of query
    for i in range(len(postIDs)):
        if postTypes[i] == 0:
            questionList.append(postIDs[i])
        else:
            answerList.append(postIDs[i])

    answers = StackQuora.Answers.objects.filter(aid__in = answerList)
    for answer in answers:
        questionList.append(answer.parentid)

    questions = StackQuora.Questions.objects.filter(qid__in = questionList)

    for i in range(len(postIDs)):
        post = None
        postTitle = ''
        if res[i] == 0:
            post = filter(lambda x: x.qid == postIDs[i], questions)[0]
            postTitle = post.title
        else:
            post = filter(lambda x: x.aid == postIDs[i], answers)[0]
            postTitle = (filter(lambda x: x.qid == post.parentid, questions)[0]).title

        res[i] = {'postID':postIDs[i], 'userID':post.owneruserid, 'title': postTitle, 'body': post.body, 'upVotes':post.upvote, 'downVotes':post.downvote, 'creationDate': post.creationdate.strftime(TIME_FORMAT)}

    users = StackQuora.Users.objects.filter(uid__in = [post['userID'] for post in res])
    for postDetail in res:
        # user related information 
        user = (filter(lambda x: x.uid == postDetail['userID'], users))[0]
        postDetail['author'] = user.username
        postDetail['reputation'] = user.reputation

    return res

def getCertainActivities(userID, postType, actionType, page):
    showPost = 3
    if postType != 2:
        showPost = 1 << postType

    showAction = 7
    if actionType != 3:
        showAction = 1 << actionType
    activities = getUserActivities([userID], pageOffset=page, showActionType=showAction, showPostType = showPost)
    res = {"recentActivities": activities["recentActivities"]}

    # get post detail
    postIDs = []
    postTypes = []
    for activity in res['recentActivities']:
        postIDs.append(activity["postID"])
        postTypes.append(activity["postType"])

    res["postDetail"] = getPosts(postIDs, postTypes)
    return res


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
        return HttpResponseBadRequest("No corresponding Questions/Answers \
            found in table, something is wrong, \
            check your record.")
    newactiontype = 0;
    if voteStatus == 0:
        newactiontype = 4 + postType
    elif voteStatus == 2:
        newactiontype = 2 + postType
            
        # query = "SELECT * FROM ActivityHistory WHERE uid = {} and actionid = {} and (actiontype > 1 and actiontype < 6 and actiontype % 2 == {})".format(userID, postID, postType)

    # suggestion, instead of using raw query set, maybe:
    query_res = StackQuora.Activityhistory.objects.filter(uid = userID, actionid = postID)
    res = []
    for an_result in query_res:
        if an_result.actiontype >1 and an_result.actiontype < 6 and an_result.actiontype % 2 == postType:
            res.append(an_result)   


    # res = StackQuora.Activityhistory.objects.raw(query)
    if len(res) == 0  and voteStatus != 1:
        #query = "INSERT INTO ActivityHistory (uid, actionid, actiontype, time) value ({}, {}, )".format(userID, postID, actiontype)
        # activity = StackQuora.Activityhistory.objects.create(uid = userID, actionid = postID, 
        #   actiontype = newactiontype, time = datetime.datetime.utcnow())
        
        uid=userID
        actionid = postID
        actiontype = newactiontype
        time = datetime.datetime.utcnow()

        # cursor used to execute raw query
        cursor = connection.cursor()
        query = '''INSERT INTO ActivityHistory (uID, actionID, actionType, time)
                    VALUES (%s,%s,%s,%s)
                '''

        cursor.execute(query,[uid,actionid,actiontype,time])

        if voteStatus == 0:
            data.downvote += 1
        else:
            data.upvote += 1
            
    if len(res) != 0:
        for vote in res:
            if vote.actiontype == 2 or vote.actiontype == 3:
                data.upvote -= 1
            else:
                data.downvote -= 1
            if voteStatus == 1:
                uid = userID
                actionid = postID
                cursor = connection.cursor()

                # incase the user reset its own question 
                # which is highly unlikely, but it can happen.
                query = '''DELETE FROM ActivityHistory 
                           WHERE uID = %s and actionID = %s
                           and actionType != %s and actionType !=%s 
                        '''
                cursor.execute(query,[uid,actionid,1,0])
            else:
                cursor = connection.cursor()
                query = '''UPDATE ActivityHistory 
                           SET actionType = %s
                           WHERE uID = %s and actionID = %s
                        '''
                cursor.execute(query,[newactiontype, userID, postID])
                # vote.actiontype = newactiontype
    data.save()

    # update recommandation system

    return HttpResponse("Success!")

# getUserUpdate
# input: uID
# output: short version question JSON specified on stackoverflow issue
# side-effect: none
# description: first stage will only randomly return ten questions
#               will return actual questions that is related later on.
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
#       ques, specify whether a question an all of its answers will return
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
def displayQuestionAnswers(qaID, is_answ):
    data_json = {}
    questionAuther = ()
    aAuthorID = []
    answerAuthors = []
    if not is_answ:
        # try to get questions specified by qaID
        try:
            req_question = StackQuora.Questions.objects.get(qid = qaID)
        except ObjectDoesNotExist:
            return HttpResponseBadRequest("qID no longer exist in the database")

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
            return HttpResponseBadRequest("aID no longer exist in the database")
        answerAuthor = StackQuora.Users.objects.get(uid = req_answer.owneruserid)
        answerAuthors.append((answerAuthor.username,answerAuthor.reputation, answerAuthor.uid))
        data_json = json_parser.json_displayQuestionAnswers(None, 
            [req_answer], [], ("",0), answerAuthors)
    return JsonResponse(data_json)


# delete a post, could either be an answer or a question
# input: ID, qid or aid, is_ques specify whether this is 
#   an answer or not
# side effect: delete corresponding database entry
def deletePost(ID, is_answ):
    # if deleting a question, all other things has to be deleted
    if not is_answ:
        has_answer = True
        has_tag = True
        try:
            question = StackQuora.Questions.objects.get(qid = ID)
        except ObjectDoesNotExist:
            return HttpResponseBadRequest("qID no longer exist in the database.")
        
        try:
            answers = StackQuora.Answers.objects.filter(parentid = question.qid)
        except ObjectDoesNotExist:
            has_answer = False
        
        try:
            tags = StackQuora.Tags.objects.filter(tid = question.qid)
        except ObjectDoesNotExist:
            has_tag = False

        if has_answer:
            # delete all answer in activity history
            for ele in answers:
                cursor = connection.cursor()
                query = '''DELETE FROM ActivityHistory 
                        WHERE actionid = %s '''
                cursor.execute(query,[ele.aid])
            answers.delete()

        if has_tag:
            tags.delete()

        question.delete()

    # else if we are deleting answer
    else:
        try:
            answer = StackQuora.Answers.objects.get(aid = ID)
        except ObjectDoesNotExist:
            return HttpResponseBadRequest("aID no longer exist in the database.") 
        answer.delete()

    # chagne user activity history
    # delete every information related to the post
    cursor = connection.cursor()
    query = '''DELETE FROM ActivityHistory 
            WHERE actionid = %s '''
    cursor.execute(query,[ID])
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
        return HttpResponseBadRequest("No corresponding user exists: {}".format(int(answer_content['userID'])))
    
    try:
        StackQuora.Questions.objects.get(qid = int(answer_content['parentID']))
    except ObjectDoesNotExist:
        return HttpResponseBadRequest("No corresponding question exists.")

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
        return HttpResponseBadRequest("IntegrityError occured, check your pkey.")

    # add user activity history
    # cursor used to execute raw query
    cursor = connection.cursor()
    query = '''INSERT INTO ActivityHistory (uID, actionID, actionType, time)
                VALUES (%s,%s,%s,%s)
            '''
    cursor.execute(query,[owneruserID,aID,1,creationDate])

    return HttpResponse("Answer added.")

# post Question, used to post question from a user
# this function should only be exposed to user if user is logged in
# otherwise, exception will be thrown
def postQuestion(body):
    inJson = json.loads(body)
    question_content = inJson['content'] 
    try:
        StackQuora.Users.objects.get(uid = int(question_content['userID']))
    except ObjectDoesNotExist:
        return HttpResponseBadRequest("No corresponding user exists: {}".format(int(question_content['userID'])))
    
    max_ = StackQuora.Questions.objects.aggregate(Max('qid'))['qid__max']
    
    qID  = max_+1
    owneruserID = int(question_content['userID'])
    creationDate = datetime.datetime.utcnow()
    title = question_content['title']
    body = question_content['body']
    tags = question_content['tags']
    creationDate = datetime.datetime.utcnow()
    score = 0
    upVote = 0
    downVote = 0
    private = 0

    # create question leave closedDate to be NULL
    try:
        new_question = StackQuora.Questions.objects.create(qid = qID, owneruserid = owneruserID,
            body = body, score = score, creationdate = creationDate, 
            upvote = upVote, downvote = downVote, private = private, title = title)
    except:
        return HttpResponseBadRequest("IntegrityError occured in question, check your pkey.")

    # if pass, insert tags
    for tag in tags:
        try:
            new_tag = StackQuora.Tags.objects.create(tid = qID, tags = tag)
        except:
            return HttpResponseBadRequest("IntegrityError occured in tags, check your pkey.")
    
    # add user activity history
    # cursor used to execute raw query
    cursor = connection.cursor()
    query = '''INSERT INTO ActivityHistory (uID, actionID, actionType, time)
                VALUES (%s,%s,%s,%s)
            '''
    cursor.execute(query,[owneruserID,qID,0,creationDate])

    return HttpResponse("Question added.")

# function update followers
# input: userID, targetID, type
# output: none
# side-effect: follower-following pair inserted into database
def updateFollowers(body):
    inJson = json.loads(body)
    userID = int(inJson['userID'])
    targetID = int(inJson['targetID'])
    typ = int(inJson['type'])

    if userID == targetID:
        return HttpResponse("LOL, user cannot follow himself, loop is not allowed!")

    try:
        user = StackQuora.Users.objects.get(uid = userID)
        target = StackQuora.Users.objects.get(uid = targetID)        
    except ObjectDoesNotExist:
        return HttpResponseBadRequest("Either user or target user doesn't exist.")

    # find if the user is following the target
    if typ == 1:
        try:
            res = StackQuora.Following.objects.get(uid = userID, uidfollowing = targetID)
        except ObjectDoesNotExist:
            return HttpResponseBadRequest("User-target pair does not exists!")
        cursor = connection.cursor()
        query = '''DELETE FROM Following 
                    WHERE uID = %s and uIDFollowing = %s
                '''
        cursor.execute(query,[userID, targetID])
        user.following = user.following - 1
        target.follower = target.follower - 1
        user.save()
        target.save()
        return HttpResponse("Successfully deleted pair!")
    else:
        try:
            res = StackQuora.Following.objects.get(uid = userID, uidfollowing = targetID)
        except ObjectDoesNotExist:
            user.following = user.following+1
            target.follower = target.follower+1
            user.save()
            target.save()
            new_pair = StackQuora.Following.objects.create(uid = userID, uidfollowing = targetID)
            return HttpResponse("Successfully add pair!")
    return HttpResponse("Pair already exists!")

# function updates userName, 
# we only have userName right now
def updateUserInfo(body):
    inJson = json.loads(body)
    userID = int(inJson['userID'])
    userName = inJson['userName']
    try:
        res = StackQuora.Users.objects.get(uid = userID)
    except ObjectDoesNotExist:
        return HttpResponseBadRequest("User doesn't exist.")
    
    res.username = userName
    res.save()
    return HttpResponse("Successfully update the name!")

# little helper function that gets qID from aID
# database is indexed on p-key so we are good.
def getqIDfromaID(aID):
    try:
        res = StackQuora.Answers.objects.get(aid = aID)
    except:
        return HttpResponseBadRequest("Answer with aID passed in doesn't exists.")
    return HttpResponse(res.parentid)