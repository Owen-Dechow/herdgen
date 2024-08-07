from django.http import HttpRequest
from django.shortcuts import render
from . import forms


# Create your views here.
def homepage(request: HttpRequest):
    return render(request, "base/homepage.html")


def signup(request: HttpRequest):
    if request.method == "POST":
        form = forms.UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.login()

    else:
        form = forms.UserCreationForm()

    return render(request, "registration/register.html", {"form": form})
