from multiprocessing import context
from django.shortcuts import redirect, render
from .models import Room, Topic, Message
# Create your views here.
from .forms import RoomForm
from django.db.models import Q
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm


def loginPage(request):
    page = "login"
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == "POST":
        username = request.POST.get('username').lower()
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)
        if user:
            auth.login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Inavlid Credentials')
            return redirect('login')

    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    auth.logout(request)
    return redirect('login')


def registerPage(request):
    form = UserCreationForm()
    context = {'form': form}

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            return redirect('login')
        else:
            messages.error(request, 'An error ocurred during registration')
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
    room_count = rooms.count()
    topic = Topic.objects.all()

    room_messages = Message.objects.filter(room__topic__name__icontains=q)

    context = {'rooms': rooms, 'topics': topic,
               'rooms_count': room_count, 'room_messages': room_messages}
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
    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            room=form.save(commit=False)
            room.host=request.user
            room.save()
            return redirect('home')
    context = {'form': form}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='/login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)  # update room
        if form.is_valid():
            form.save()
            return redirect('home')
    context = {'form': form}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='/login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    if request.method == "POST":
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_message = user.message_set.all()
    topic = Topic.objects.all()
    context = {'user': user, 'rooms': rooms,
               'room_messages': room_message, 'topics': topic}
    return render(request, 'base/profile.html', context)
