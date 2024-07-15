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
            return redirect('login')  # Redirect to login page after successful registration
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

@login_required
def vote_view(request):
    categories_with_candidates = Category.objects.filter(candidate__isnull=False).distinct()
    
    if request.method == 'POST':
        selected_candidate_id = request.POST.get('candidate')
        category_id = request.POST.get('category')
        
        # Check if a candidate was selected
        if not selected_candidate_id:
            return render(request, 'vote.html', {'categories': categories_with_candidates, 'error_message': 'Please select a candidate to vote.'})
        
        # Check if the user has already voted in this category
        if Vote.objects.filter(student=request.user, category_id=category_id).exists():
            return render(request, 'already_voted.html')

        try:
            candidate = Candidate.objects.get(id=selected_candidate_id)
            category = Category.objects.get(id=category_id)
            
            # Create a new Vote object for the selected candidate and category
            Vote.objects.create(student=request.user, candidate=candidate, category=category)
            return redirect('thank_you')
        
        except Candidate.DoesNotExist:
            return HttpResponseBadRequest('Invalid candidate selection.')
        except Category.DoesNotExist:
            return HttpResponseBadRequest('Invalid category selection.')

    return render(request, 'vote.html', {'categories': categories_with_candidates})








def thank_you_view(request):
    return render(request, 'thank_you.html')

