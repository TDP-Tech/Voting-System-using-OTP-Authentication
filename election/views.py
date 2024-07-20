# election/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from django.http import HttpResponseBadRequest, JsonResponse
from django.db.models import Count, Max, Q, Sum
from election.models import Vote, Candidate, Category, ElectionSettings
from .forms import LoginForm, VoteForm, RegistrationForm
import json, base64
from django.utils import timezone
from pytz import timezone as pytz_timezone
from datetime import datetime

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
                otp = user.generate_otp()
                user_name = user.student_id
                send_mail(
                    'OTP Code for Authenticating you in Poll Station',
                    f'{user_name} your OTP code is {otp}, it will expire within 10 minutes',
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

def otp_verification_view(request):
    if request.method == 'POST':
        otp_entered = request.POST.get('otp_code')
        if request.user.is_authenticated:
            otp_valid, otp_expired = request.user.is_otp_valid(otp_entered)
            if otp_valid:
                return redirect('vote')
            elif otp_expired:
                messages.error(request, 'OTP Code has expired')
            else:
                messages.error(request, 'Invalid OTP Code')
        else:
            messages.error(request, 'User is not authenticated')
    return render(request, 'otp_verification.html')

@login_required
def vote_view(request):
    # Get the election title
    election_settings = ElectionSettings.objects.first()
    
    tanzania_tz = pytz_timezone('Africa/Dar_es_Salaam')
    categories_with_candidates = Category.objects.filter(candidate__isnull=False).distinct()

    current_time = timezone.now().astimezone(tanzania_tz)
    current_year = datetime.now().year

    if request.method == 'POST':
        selected_candidate_id = request.POST.get('candidate')
        category_id = request.POST.get('category')

        if not selected_candidate_id:
            return render(request, 'vote.html', {
                'categories': categories_with_candidates,
                'election_title': election_settings.title if election_settings else "Default Title",
                'current_year': current_year,
                'error_message': "You haven't selected any leader. Refresh the page and select a leader, then click the Submit Vote button."
            })

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

    for category in categories_with_candidates:
        if category.voting_start_time and current_time < category.voting_start_time:
            category.voting_status = 'Not Started'
            category.remaining_time = category.voting_start_time - current_time
        elif category.voting_end_time and current_time > category.voting_end_time:
            category.voting_status = 'Ended'
            category.remaining_time = 0
        else:
            category.voting_status = 'Ongoing'
            category.remaining_time = category.voting_end_time - current_time if category.voting_end_time else 0

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

    return render(request, 'vote.html', {
        'categories': categories_with_candidates,
        'election_title': election_settings.title if election_settings else "XYZ University",
        'current_year': current_year
    })

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


def vote_analytics_view(request):
    categories_with_candidates = Category.objects.filter(candidate__isnull=False).distinct()

    analytics = []
    for category in categories_with_candidates:
        candidates = category.candidate_set.annotate(vote_count=Count('vote')).order_by('-vote_count')
        total_votes = candidates.aggregate(total_votes=Sum('vote_count'))['total_votes']

        category_analytics = {
            'category_id': category.id,
            'category_name': category.category_name,
            'candidates': []
        }

        for candidate in candidates:
            vote_count = candidate.vote_count
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            category_analytics['candidates'].append({
                'candidate_id': candidate.id,
                'name': f"{candidate.first_name} {candidate.last_name}",
                'vote_count': vote_count,
                'percentage': percentage
            })

        analytics.append(category_analytics)

    return render(request, 'vote_analytics.html', {'categories': analytics})

def thank_you_view(request):
    return render(request, 'thank_you.html')

def already_voted(request):
    return render(request, 'already_voted.html')

@login_required
def election_results_view(request):
    tanzania_tz = pytz_timezone('Africa/Dar_es_Salaam')
    categories_with_candidates = Category.objects.filter(candidate__isnull=False).distinct()
    current_time = timezone.now().astimezone(tanzania_tz)

    for category in categories_with_candidates:
        candidates = category.candidate_set.annotate(vote_count=Count('vote')).order_by('-vote_count')
        category.candidates_with_votes = candidates

    return render(request, 'electionresults.html', {'categories': categories_with_candidates})

@login_required
def winners_view(request):
    tanzania_tz = pytz_timezone('Africa/Dar_es_Salaam')
    categories_with_candidates = Category.objects.filter(candidate__isnull=False).distinct()
    current_time = timezone.now().astimezone(tanzania_tz)

    all_winners = []

    for category in categories_with_candidates:
        # Check if voting time is finished
        if category.voting_end_time and current_time > category.voting_end_time:
            candidates = category.candidate_set.annotate(vote_count=Count('vote')).order_by('-vote_count')
            max_votes = candidates.first().vote_count if candidates else 0
            winners = candidates.filter(vote_count=max_votes)
            all_winners.extend(winners)  # Add winners to the list

    # Remove duplicates while maintaining order
    all_winners = list(dict.fromkeys(all_winners))

    return render(request, 'winners.html', {'winners': all_winners})


