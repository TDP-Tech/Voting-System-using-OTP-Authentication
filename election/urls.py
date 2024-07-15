from django.urls import path
from .views import login_view, vote_view, thank_you_view, register_view, otp_verification_view, logout_view
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('vote/', vote_view, name='vote'),
    path('thank_you/', thank_you_view, name='thank_you'),
     path('otp/', otp_verification_view, name='otp_verification'),
     path('logout/', logout_view, name='logout'),
     
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)