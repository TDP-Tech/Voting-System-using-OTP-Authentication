from django.urls import path
from .views import login_view, vote_view, already_voted,thank_you_view, register_view, otp_verification_view, logout_view, winners_view, election_results_view
from .views import vote_analytics_view
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    #Authentication
    path('register/', register_view, name='register'),
    path('', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    #Authentication Verification
    path('otp/', otp_verification_view, name='otp_verification'),
    #Voting
    path('vote/', vote_view, name='vote'),
    path('already_voted/',already_voted, name='already_voted'),
    path('thank_you/', thank_you_view, name='thank_you'),
    #Analytics
    path('vote_analytics/', vote_analytics_view, name='vote_analytics'),
    #Results
    path('election-results/', election_results_view, name='election_results'),
    path('winners/', winners_view, name='winners'),  
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)