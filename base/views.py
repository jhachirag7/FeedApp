from django.shortcuts import redirect, render
from .models import Room, Topic, Message, Profile
# Create your views here.
from .forms import RoomForm, UserForm
from django.db.models import Q, Count
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
import json
from django.http import JsonResponse
from django.views import View
from validate_email import validate_email
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from FeedApp import settings
from .token import generateToken


import threading


class EmailTread(threading.Thread):

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send(fail_silently=False)


def loginPage(request):
    page = "login"
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == "POST":
        username = request.POST.get('username').lower()
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)
        if user and user.is_active:
            auth.login(request, user)
            return redirect('home')
        else:
            messages.error(
                request, 'Inavlid Credentials or account not activated')
            return redirect('login')

    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    auth.logout(request)
    return redirect('login')


def registerPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = UserCreationForm()
    context = {'form': form}

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        email = request.POST['email']
        exists = User.objects.filter(email=email).exists()
        # existsu=User.objects.filter(user=form.fields['username']).exists()
        if form.is_valid() and exists == False:
            email = email.strip()
            user = form.save(commit=False)
            current_site = get_current_site(request)
            email_subject = "Confirm Your email @FeedApp!!"

            message = render_to_string('base/email_confirmation.html', {
                'name': user.username,
                'emai': email,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': generateToken.make_token(user),
            })
            email = EmailMessage(
                email_subject,
                message,
                settings.EMAIL_HOST_USER,
                [email],
            )
            EmailTread(email).start()
            user.username = user.username.lower()
            user.save()
            user.email = email
            user.is_active = False
            user.save()

            messages.success(
                request, "Account successfully created for activation confirm your mail from your accounts")
            return redirect('login')
        else:
            messages.error(request, 'InValid Credentials')
    return render(request, 'base/login_register.html', context)


@login_required(login_url='/login')
def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    q = q.strip()
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )
    rooms = rooms.annotate(count=Count('participants')).order_by('-count')
    room_count = rooms.count()
    topic = Topic.objects.annotate(count=Count(
        'room__topic__name')).order_by('-count')[0:7]

    room_messages = Message.objects.filter(room__topic__name__icontains=q)[0:4]
    profile = None
    try:
        profile = Profile.objects.get(user=request.user)
    except:
        pass
    profiles = Profile.objects.all()
    context = {'rooms': rooms, 'topics': topic,
               'rooms_count': room_count, 'room_messages': room_messages, 'profile': profile, 'profiles': profiles}
    return render(request, 'base/home.html', context)


@login_required(login_url='/login')
def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()

    if request.method == "POST":
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST['body']
        )
        room.participants.add(request.user)
        return redirect('room', pk=pk)
    context = {'room': room, 'room_messages': room_messages,
               'participants': participants}
    return render(request, 'base/room.html', context)


@login_required(login_url='/login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    room = Room.objects.get(name=message.room)
    if request.method == "POST":
        message.delete()
        return redirect('room', room.id)
    return render(request, 'base/delete.html', {'obj': message})


@login_required(login_url='/login')
def createRoom(request):
    form = RoomForm()
    topic = Topic.objects.all()
    if request.method == "POST":
        topic_name = request.POST['topic']
        old_topic, created = Topic.objects.get_or_create(name=topic_name)
        Room.objects.create(
            host=request.user,
            topic=old_topic,
            name=request.POST['name'],
            description=request.POST['description']
        )
        return redirect('home')
    context = {'form': form, 'topics': topic}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='/login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topic = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST['topic']
        old_topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST['name']
        room.topic = old_topic
        room.description = request.POST['description']
        room.save()
        return redirect('home')
    context = {'form': form, 'topics': topic, 'room': room}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='/login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    if request.method == "POST":
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})


@login_required(login_url='/login')
def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_message = user.message_set.all()
    topic = Topic.objects.all()
    profile = None
    try:
        profile = Profile.objects.get(user=user)
    except:
        pass
    context = {'user': user, 'rooms': rooms,
               'room_messages': room_message, 'topics': topic, 'profile': profile}
    return render(request, 'base/profile.html', context)


@login_required(login_url='/login')
def updateUser(request):
    user = request.user
    exists = Profile.objects.filter(user=user).exists()
    form = UserForm(instance=user)
    if exists:
        profile = Profile.objects.get(user=user)
        form = UserForm(instance=user, initial={
                        'name': profile.name, 'Bio': profile.Bio, })

    if request.method == "POST":
        name = request.POST['name']
        bio = request.POST['Bio']
        img = request.FILES['image']

        if exists:
            profile = Profile.objects.get(user=user)
            profile.name = name
            profile.Bio = bio
            profile.image = img
            profile.save()
        else:
            Profile.objects.create(user=user, name=name, Bio=bio, image=img)
        return redirect('user-profile', pk=user.id)

    context = {'form': form}
    return render(request, 'base/update_user.html', context)


def topicPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    q = q.strip()
    topics = Topic.objects.filter(name__icontains=q)
    context = {'topics': topics}
    return render(request, 'base/topics.html', context)


def activityPage(request):
    room_messages = Message.objects.all()
    context = {'room_messages': room_messages}
    return render(request, 'base/activity.html', context)


class UsernameValidate(View):
    def post(self, request):
        data = json.loads(request.body)
        username = data['username']
        username = username.lower()

        if User.objects.filter(username=username).exists():
            return JsonResponse({'username_error': 'username already taken'}, status=409)
        return JsonResponse({'username_valid': True})


class EmailValidate(View):
    def post(self, request):
        data = json.loads(request.body)
        email = data['email']

        if not validate_email(email):
            return JsonResponse({'email_error': 'Mail format is not correct'}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'email_error': 'email already taken'}, status=409)
        return JsonResponse({'email_valid': True})


class EmailActivation(View):
    def get(self, request, uid64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uid64))
            user = User.objects.get(pk=uid)
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and generateToken.check_token(user, token):
            user.is_active = True
            user.save()
            return redirect('login')
        else:
            return render(request, "base/activation_failed.html")
