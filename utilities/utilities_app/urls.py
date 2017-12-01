from django.conf.urls import url
from . import views

# remember to restart apache server to keep url up to date
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^user/following/checkList$',views.getFollowingStatus),
    url(r'^post/vote/checkList$',views.getVoteStatus),
    url(r'^user/status/(?P<userID>[0-9]+)/(?P<showActivities>[01]{1})',views.getUserStatus),
    url(r'^user/following/timeline/(?P<userID>[0-9]+)/(?P<page>[0-9]+)', views.getFollowingActivities),
    url(r'^post/vote/(?P<postID>[0-9]+)/(?P<postType>[0-1]{1})/(?P<userID>[0-9]+)/(?P<voteStatus>[0-2]{1})/$',views.updateVoteStatus),
    url(r'^userUpdateRandom/$', views.getUserUpdate_random),
    url(r'^displayQuestionAnswers/(?P<qaID>[0-9]+)/(?P<is_ques>[0-1]{1})/$', 
        views.displayQuestionAnswers),
    url(r'^post/postAnswer/$',views.postAnswer),
    url(r'^post/postQuestion/$',views.postQuestion),
    url(r'^post/deletePost/(?P<ID>[0-9]+)/(?P<is_ques>[0-9]+)/$',views.deletePost),
    url(r'^user/(?P<requestType>followings|followers)/(?P<userID>[0-9]+)/(?P<page>[0-9]+)/(?P<showDetail>[01]{1})', views.getFollows),
    url(r'^user/filteredTimeline/(?P<userID>[0-9]+)/(?P<postType>[0-2]{1})/(?P<actionType>[0-3]{1})/(?P<page>[0-9]+)', views.getCertainActivities),
    url(r'^user/updateFollowers/$', views.updateFollowers),
    url(r'^user/updateUserInfo/$', views.updateUserInfo),
    url(r'^getqIDfromaID/(?P<aID>[0-9]+)/$',views.getqIDfromaID),
]