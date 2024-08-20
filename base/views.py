from time import sleep
from django.http import (
    Http404,
    HttpRequest,
    HttpResponseRedirect,
    HttpResponse,
    JsonResponse,
)
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db import transaction
from django.views.decorators.http import require_POST
from . import forms
from . import models
from .views_utils import HerdAuth, auth_class, ClassAuth, auth_herd


# Create your views here.
def homepage(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        owned_classes = models.Class.objects.filter(teacher=request.user)
        enrollments = models.Enrollment.objects.select_related("connectedclass").filter(
            student=request.user
        )
        classes = list(owned_classes) + [x.connectedclass for x in enrollments]
        classes = {x: models.Assignment.objects.all() for x in classes}

        requested_classes = [
            x.connectedclass
            for x in models.EnrollmentRequest.objects.select_related(
                "connectedclass"
            ).filter(student=request.user)
        ]
    else:
        classes = requested_classes = []

    return render(
        request,
        "base/homepage.html",
        {"classes": classes, "requested_classes": requested_classes},
    )


@transaction.atomic
def signup(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = forms.UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return HttpResponseRedirect("/")

    else:
        form = forms.UserCreationForm()

    return render(request, "registration/register.html", {"form": form})


@login_required
@transaction.atomic
def createclass(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = forms.CreateClassForm(request.POST)
        if form.is_valid():
            connectedclass = form.save(request.user)
            return HttpResponseRedirect(f"/class/{connectedclass.id}")
    else:
        form = forms.CreateClassForm

    return render(request, "base/createclass.html", {"form": form})


@transaction.atomic
@login_required
def openclass(request: HttpRequest, classid: int) -> HttpResponse:
    class_auth = auth_class(request, classid)
    connectedclass = class_auth.connectedclass

    if type(class_auth) is ClassAuth.Teacher:
        enrollment = None
        if request.method == "POST":
            form = forms.UpdateClassForm(request.POST, instance=connectedclass)
            if form.is_valid():
                form.save()
        else:
            form = forms.UpdateClassForm(instance=connectedclass)

    elif type(class_auth) is ClassAuth.Student:
        enrollment = class_auth.enrollment
        form = forms.ClassReadonlyForm(instance=connectedclass)

    return render(
        request,
        "base/openclass.html",
        {"class": connectedclass, "form": form, "enrollment": enrollment},
    )


@transaction.atomic
@login_required
@require_POST
def deleteclass(request: HttpRequest, classid: int) -> HttpResponseRedirect:
    class_auth = auth_class(request, classid)
    if type(class_auth) is not ClassAuth.Teacher:
        raise HttpRequest("Must be teacher to delete class")

    class_auth.connectedclass.delete()
    return HttpResponseRedirect("/")


@transaction.atomic
@login_required
def joinclass(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = forms.JoinClass(request.user, request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(f"/class/requested")
    else:
        form = forms.JoinClass

    return render(request, "base/joinclass.html", {"form": form})


@login_required
def requestedclass(request: HttpRequest) -> HttpResponse:
    return render(request, "base/requestedclass.html", {})


@login_required
def openherd(request: HttpRequest, classid: int, herdid: int) -> HttpResponse:
    class_auth = auth_class(request, classid)
    herd_auth = auth_herd(class_auth, herdid)

    context = {}
    if type(class_auth) is ClassAuth.Student:
        context = {"enrollment": class_auth.enrollment}

    context["class"] = class_auth.connectedclass
    context["herd_auth"] = herd_auth
    context["herd_auth_type"] = type(herd_auth)
    context["enrollment_herd"] = HerdAuth.EnrollmentHerd
    context["breed_form"] = forms.BreedHerd

    return render(request, "base/openherd.html", context)


# GET JSON
@login_required
def get_enrollments(request: HttpRequest, classid: int) -> JsonResponse:
    class_auth = auth_class(request, classid)

    if type(class_auth) != ClassAuth.Teacher:
        return Http404("Must be teacher to get_enrollments")

    json = {
        "enrollments": [
            x.json_dict()
            for x in models.Enrollment.objects.filter(
                connectedclass=class_auth.connectedclass
            )
        ],
        "enrollment_requests": [
            x.json_dict()
            for x in models.EnrollmentRequest.objects.filter(
                connectedclass=class_auth.connectedclass
            )
        ],
    }

    return JsonResponse(json)


@login_required
def get_herd(request: HttpRequest, classid: int, herdid: int) -> JsonResponse:
    class_auth = auth_class(request, classid)
    herd_auth = auth_herd(class_auth, herdid)

    return JsonResponse(herd_auth.herd.json_dict())


@login_required
def get_assignments(request: HttpRequest, classid: int, herdid: int) -> JsonResponse:
    class_auth = auth_class(request, classid)
    herd_auth = auth_herd(class_auth, herdid)

    if type(herd_auth) is not HerdAuth.EnrollmentHerd:
        raise Http404("Invalid herd to collect assignments for.")

    assignments = class_auth.enrollment.get_open_assignments_json_dict()
    return JsonResponse(assignments)


@login_required
def get_breeding_validation(
    request: HttpRequest, classid: int, herdid: int
) -> JsonResponse:
    form = forms.BreedHerd(request.GET)
    class_auth = auth_class(request, classid)
    herd_auth = auth_herd(class_auth, herdid)

    if type(class_auth) is not ClassAuth.Student:
        raise Http404("Must be student to breed herd")

    if type(herd_auth) is not HerdAuth.EnrollmentHerd:
        raise Http404("Must be enrollment herd to breed")

    if form.is_valid(class_auth):
        return JsonResponse({"status": "pass"})
    else:
        return JsonResponse({"status": "fail"})


@transaction.atomic
@login_required
@require_POST
def breed_herd(request: HttpRequest, classid: int, herdid: int):
    form = forms.BreedHerd(request.POST)
    class_auth = auth_class(request, classid)
    herd_auth = auth_herd(class_auth, herdid)

    if type(class_auth) is not ClassAuth.Student:
        raise Http404("Must be student to breed herd")

    if type(herd_auth) is not HerdAuth.EnrollmentHerd:
        raise Http404("Must be enrollment herd to breed")

    if form.is_valid(class_auth):
        form.save(class_auth, herd_auth)
    else:
        raise Http404(f"Breeding is invalid: {form.errors}")


# ACTION
@login_required
@transaction.atomic
@require_POST
def confirm_enrollment(
    request: HttpRequest, classid: int, requestid: int
) -> JsonResponse:
    class_auth = auth_class(request, classid)

    if type(class_auth) != ClassAuth.Teacher:
        return Http404("Must be teacher to confirm enrollment")

    if class_auth.connectedclass.enrollment_tokens > 0:
        enrollment_request = get_object_or_404(
            models.EnrollmentRequest.objects.select_related(
                "connectedclass", "student"
            ),
            id=requestid,
            connectedclass=class_auth.connectedclass,
        )

        enrollment = models.Enrollment.create_from_enrollment_request(
            enrollment_request
        )

        data = enrollment.json_dict()
    else:
        data = {"out of tokens": True}

    return JsonResponse(data)


@login_required
@transaction.atomic
@require_POST
def remove_enrollment(
    request: HttpRequest, classid: int, enrollmentid: int
) -> JsonResponse:
    class_auth = auth_class(request, classid)

    if type(class_auth) != ClassAuth.Teacher:
        return Http404("Must be teacher to deny enrollment")

    enrollment = get_object_or_404(
        models.Enrollment, id=enrollmentid, connectedclass=class_auth.connectedclass
    )
    enrollment.delete()

    return JsonResponse({})


@login_required
@transaction.atomic
@require_POST
def deny_enrollment(request: HttpRequest, classid: int, requestid: int) -> JsonResponse:
    class_auth = auth_class(request, classid)

    if type(class_auth) != ClassAuth.Teacher:
        return Http404("Must be teacher to deny enrollment")

    enrollment_request = get_object_or_404(
        models.EnrollmentRequest, id=requestid, connectedclass=class_auth.connectedclass
    )
    enrollment_request.delete()

    return JsonResponse({})
