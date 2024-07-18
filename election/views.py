# election/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import LoginForm, VoteForm, RegistrationForm
from election.models import Vote, Candidate, Category
from django.contrib import messages
from django.http import JsonResponse
import json, base64
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from .utils import get_user_public_key

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            student = form.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    message = request.GET.get('message', '')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            student_id = form.cleaned_data['student_id']
            password = form.cleaned_data['password']
            user = authenticate(request, student_id=student_id, password=password)
            if user is not None:
                login(request, user)
                otp = user.generate_otp()  # Assuming you have a method to generate OTP for the user
                send_mail(
                    'Your OTP Code',
                    f'Your OTP code is {otp}',
                    'tanzaniadigitalprojectstech@gmail.com',
                    [user.email],
                    fail_silently=False,
                )
                return redirect('otp_verification')
            else:
                return render(request, 'login.html', {'form': form, 'error_message': 'Invalid credentials', 'message': message})
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

################ OTP VERIFICATION ##############
def otp_verification_view(request):
    if request.method == 'POST':
        otp_entered = request.POST.get('otp_code')
        if request.user.is_authenticated and request.user.is_otp_valid(otp_entered):
            # Assuming is_otp_valid is a method in your User model to validate OTP
            return redirect('vote')  # Redirect to vote page upon successful OTP verification
        else:
            messages.error(request, 'Invalid OTP or OTP has expired')
    return render(request, 'otp_verification.html')

############ END OF OTP VERIFICATION ###########

################ FINGERPRINT VERIFICATION ##############
@csrf_exempt
def fingerprint_auth_view(request):
    if request.method == 'POST':
        # Verify the fingerprint credential here
        credential = json.loads(request.body)
        # If verification is successful
        if verify_credential(credential):
            login(request, request.user)
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'failure'}, status=400)


def verify_credential(credential):
    # Decode and verify the credential with your server-side logic
    client_data = base64.urlsafe_b64decode(credential['response']['clientDataJSON'])
    authenticator_data = base64.urlsafe_b64decode(credential['response']['authenticatorData'])
    signature = base64.urlsafe_b64decode(credential['response']['signature'])
    public_key = get_user_public_key(credential['id'])

    verifier = ec.ECDSA(hashes.SHA256())
    try:
        verifier.update(client_data + authenticator_data)
        public_key.verify(signature, verifier.finalize())
        return True
    except Exception as e:
        print(f"Verification failed: {str(e)}")
        return False



############ END OF FINGERPRINT VERIFICATION ###########
# @login_required
# def vote_view(request):
#     if request.method == 'POST':
#         form = VoteForm(request.POST)
#         if form.is_valid():
#             if not Vote.objects.filter(student=request.user).exists():
#                 candidate = form.cleaned_data['candidate']
#                 Vote.objects.create(student=request.user, candidate=candidate)
#                 return redirect('thank_you')
#             else:
#                 return render(request, 'already_voted.html')
#     else:
#         form = VoteForm()
#     return render(request, 'vote.html', {'form': form})

from django.http import HttpResponseBadRequest

from django.db.models import Count

from django.db.models import Max

from django.db.models import Count, Max
from django.http import JsonResponse

from django.db.models import Count, Max, Q

@login_required
def vote_view(request):
    categories_with_candidates = Category.objects.filter(candidate__isnull=False).distinct()

    if request.method == 'POST':
        selected_candidate_id = request.POST.get('candidate')
        category_id = request.POST.get('category')

        if not selected_candidate_id:
            return render(request, 'vote.html', {'categories': categories_with_candidates, 'error_message': "You haven't selected any leader. Refresh the page and select a leader, then click the Submit Vote button."})

        if Vote.objects.filter(student=request.user, category_id=category_id).exists():
            return redirect('already_voted')

        try:
            candidate = Candidate.objects.get(id=selected_candidate_id)
            category = Category.objects.get(id=category_id)

            Vote.objects.create(student=request.user, candidate=candidate, category=category)
            return redirect('thank_you')

        except Candidate.DoesNotExist:
            return HttpResponseBadRequest('Invalid candidate selection.')
        except Category.DoesNotExist:
            return HttpResponseBadRequest('Invalid category selection.')

    categories_with_candidates = Category.objects.filter(candidate__isnull=False).distinct()
    for category in categories_with_candidates:
        candidates = category.candidate_set.annotate(vote_count=Count('vote')).order_by('-vote_count')
        category.candidates_with_votes = candidates
        category.user_has_voted = Vote.objects.filter(student=request.user, category=category).exists()

        max_votes = candidates.first().vote_count if candidates else 0
        leading_candidates = candidates.filter(vote_count=max_votes)

        if leading_candidates.count() > 1:
            category.leading_candidate_id = None
            category.tied_candidates = [candidate.id for candidate in leading_candidates]
        else:
            category.leading_candidate_id = leading_candidates.first().id if leading_candidates else None
            category.tied_candidates = []

    return render(request, 'vote.html', {'categories': categories_with_candidates})

# API endpoint to fetch updated vote counts and leader information
def get_vote_counts(request):
    categories_with_candidates = Category.objects.filter(candidate__isnull=False).distinct()

    data = []
    for category in categories_with_candidates:
        candidates = category.candidate_set.annotate(vote_count=Count('vote'))
        category_data = {
            'id': category.id,
            'candidates': [{
                'id': candidate.id,
                'vote_count': candidate.vote_count,
            } for candidate in candidates],
            'leading_candidate_id': category.leading_candidate_id,
            'tied_candidates': category.tied_candidates,
        }
        data.append(category_data)

    return JsonResponse({'categories': data})












def thank_you_view(request):
    return render(request, 'thank_you.html')

def already_voted(request):
    return render(request, 'already_voted.html')

