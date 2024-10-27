import time
from django.http import (
    FileResponse,
    Http404,
    HttpRequest,
    HttpResponseRedirect,
    HttpResponse,
    JsonResponse,
)
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.views import LoginView


from django.db import transaction
from django.views.decorators.http import require_POST

from .templatetags.animal_filters import filter_text_to_default
from base.traitsets.traitset import Traitset
from . import forms
from . import models
from .views_utils import HerdAuth, auth_class, ClassAuth, auth_herd
from django.utils.timezone import now
from . import csv


#### AUTH PAGE VIEWS ####
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


class EmailLoginView(LoginView):
    authentication_form = forms.EmailAuthenticationForm
    template = "registration/login.html"


#### PAGE VIEWS ####
def homepage(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        owned_classes = models.Class.objects.select_related("teacher").filter(
            teacher=request.user
        )
        enrollments = models.Enrollment.objects.select_related("connectedclass").filter(
            student=request.user
        )
        classes = list(owned_classes) + [x.connectedclass for x in enrollments]
        classes = {x: x.get_open_assignments() for x in classes}

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
    class_auth = auth_class(request, classid, "starter_herd", "class_herd")
    connectedclass = class_auth.connectedclass

    if type(class_auth) in ClassAuth.TEACHER_ADMIN:
        enrollment = None
        enrollment_form = None
        if request.method == "POST":
            form = forms.UpdateClassForm(
                class_auth.connectedclass, request.POST, instance=connectedclass
            )
            if form.is_valid():
                form.save()
        else:
            form = forms.UpdateClassForm(
                class_auth.connectedclass, instance=connectedclass
            )

    elif type(class_auth) is ClassAuth.Student:
        enrollment = class_auth.enrollment
        form = forms.ClassReadonlyForm(instance=connectedclass)
        enrollment_form = forms.UpdateEnrollmentForm(instance=enrollment)

    return render(
        request,
        "base/openclass.html",
        {
            "class": connectedclass,
            "form": form,
            "enrollment": enrollment,
            "enrollment_form": enrollment_form,
            "teacher_status": type(class_auth) in ClassAuth.TEACHER_ADMIN,
        },
    )


@login_required
def enrollments(request: HttpRequest, classid: int) -> HttpResponse:
    class_auth = auth_class(request, classid)
    connectedclass = class_auth.connectedclass

    if type(class_auth) not in ClassAuth.TEACHER_ADMIN:
        raise Http404("Must be teacher to access enrollment page")

    return render(request, "base/enrollments.html", {"class": connectedclass})


@transaction.atomic
@login_required
def assignments(
    request: HttpRequest, classid: int
) -> HttpResponse | HttpResponseRedirect:
    class_auth = auth_class(request, classid)
    connectedclass = class_auth.connectedclass

    if request.method == "POST":
        form = forms.NewAssignment(request.POST)
        if form.is_valid():
            assignment = form.save(connectedclass)
            return HttpResponseRedirect(f"/class/{classid}/assignments/{assignment.id}")
    else:
        form = forms.NewAssignment

    if type(class_auth) not in ClassAuth.TEACHER_ADMIN:
        raise Http404("Must be teacher to access assignments page")

    enrollments = models.Enrollment.objects.filter(
        connectedclass=connectedclass
    ).order_by("student__first_name", "student__last_name")
    assignments = [
        (
            a,
            models.AssignmentStep.objects.filter(assignment=a).count(),
            models.AssignmentFulfillment.objects.filter(assignment=a).order_by(
                "enrollment__student__first_name", "enrollment__student__last_name"
            ),
        )
        for a in models.Assignment.objects.filter(
            connectedclass=connectedclass
        ).order_by("duedate")
    ]

    return render(
        request,
        "base/assignments.html",
        {
            "class": connectedclass,
            "assignments": assignments,
            "current_date": now(),
            "enrollments": enrollments,
            "form": form,
        },
    )


@transaction.atomic
@login_required
def openassignment(
    request: HttpRequest, classid: int, assignmentid: int
) -> HttpResponse | HttpResponseRedirect:
    class_auth = auth_class(request, classid)
    assignment = get_object_or_404(models.Assignment, id=assignmentid)

    if type(class_auth) not in ClassAuth.TEACHER_ADMIN:
        raise Http404("Must be teacher to access assignments page")

    if request.method == "POST":
        form = forms.UpdateAssignment(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            HttpResponseRedirect("")
    else:
        form = forms.UpdateAssignment(instance=assignment)

    return render(
        request,
        "base/openassignment.html",
        {"form": form, "assignment": assignment, "class": class_auth.connectedclass},
    )


@transaction.atomic
@login_required
def joinclass(request: HttpRequest) -> HttpResponse | HttpResponseRedirect:
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
    class_auth = auth_class(request, classid, "starter_herd", "class_herd")
    herd_auth = auth_herd(class_auth, herdid, "enrollment")

    context = {}
    if type(class_auth) is ClassAuth.Student:
        context = {"enrollment": class_auth.enrollment}

    context["class"] = class_auth.connectedclass
    context["herd_auth"] = herd_auth
    context["collect_assignments"] = type(herd_auth) is HerdAuth.EnrollmentHerd
    context["breed_form"] = forms.BreedHerd

    return render(request, "base/openherd.html", context)


#### ACTION VIEWS ####
@require_POST
@transaction.atomic
@login_required
def update_enrollment(request: HttpRequest, classid: int) -> HttpResponseRedirect:
    class_auth = auth_class(request, classid)

    if type(class_auth) is not ClassAuth.Student:
        raise Http404("Must be student to update filter")

    form = forms.UpdateEnrollmentForm(request.POST, instance=class_auth.enrollment)
    if form.is_valid():
        form.save()
    else:
        raise Http404("Invalid enrollment update request")

    return HttpResponseRedirect(f"/class/{classid}")


@transaction.atomic
@login_required
@require_POST
def delete_assignment(
    request: HttpRequest, classid: int, assignmentid: int
) -> HttpResponseRedirect:
    class_auth = auth_class(request, classid)
    assignment = get_object_or_404(models.Assignment, id=assignmentid)

    if type(class_auth) not in ClassAuth.TEACHER_ADMIN:
        raise Http404("Must be teacher to delete assignments")

    assignment.delete()

    return HttpResponseRedirect(f"/class/{classid}/assignments")


@transaction.atomic
@login_required
@require_POST
def deleteclass(request: HttpRequest, classid: int) -> HttpResponseRedirect:
    class_auth = auth_class(request, classid)
    if type(class_auth) in ClassAuth.TEACHER_ADMIN:
        raise HttpRequest("Must be teacher to delete class")

    class_auth.connectedclass.delete()
    return HttpResponseRedirect("/")


@transaction.atomic
@login_required
@require_POST
def breed_herd(request: HttpRequest, classid: int, herdid: int) -> HttpResponseRedirect:
    form = forms.BreedHerd(request.POST)
    class_auth = auth_class(request, classid, "class_herd", "starter_herd")
    herd_auth = auth_herd(class_auth, herdid, "connectedclass")

    if type(class_auth) is not ClassAuth.Student:
        raise Http404("Must be student to breed herd")

    if type(herd_auth) is not HerdAuth.EnrollmentHerd:
        raise Http404("Must be enrollment herd to breed")

    if form.is_valid(class_auth):
        breeding_results = form.save(herd_auth)

        if breeding_results.age_deaths == 1:
            messages.info(request, "There was one death due to old age.")
        else:
            messages.info(
                request,
                f"There were {breeding_results.age_deaths} deaths due to old age.",
            )

        if breeding_results.recessive_deaths == 1:
            messages.info(
                request, "There was one death due to undesirable genetic recessives."
            )
        else:
            messages.info(
                request,
                f"There were {breeding_results.recessive_deaths} deaths due to undesirable genetic recessives.",
            )

        return HttpResponseRedirect(f"/class/{classid}/herd/{herdid}")
    else:
        raise Http404(f"Breeding is invalid: {form.errors}")


@transaction.atomic
@login_required
@require_POST
def submit_animal(
    request: HttpRequest, classid: int, herdid: int, animalid: int
) -> HttpResponseRedirect:
    form = forms.SubmitAnimal(request.POST)
    class_auth = auth_class(request, classid)
    herd_auth = auth_herd(class_auth, herdid)
    animal = get_object_or_404(
        models.Animal, connectedclass=classid, herd=herdid, id=animalid
    )

    if type(class_auth) is not ClassAuth.Student:
        raise Http404("Must be student to submit animal")

    if type(herd_auth) is not HerdAuth.EnrollmentHerd:
        raise Http404("Must be enrollment herd to submit animal")

    if form.is_valid(class_auth):
        form.save(class_auth, animal)
        return HttpResponseRedirect(f"/class/{classid}/herd/{herdid}")
    else:
        raise Http404(f"Animal submission is invalid: {form.errors}")


@login_required
@transaction.atomic
@require_POST
def confirm_enrollment(
    request: HttpRequest, classid: int, requestid: int
) -> JsonResponse:
    class_auth = auth_class(request, classid)

    if type(class_auth) not in ClassAuth.TEACHER_ADMIN:
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

    if type(class_auth) not in ClassAuth.TEACHER_ADMIN:
        return Http404("Must be teacher to remove enrollment")

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

    if type(class_auth) not in ClassAuth.TEACHER_ADMIN:
        return Http404("Must be teacher to deny enrollment")

    enrollment_request = get_object_or_404(
        models.EnrollmentRequest, id=requestid, connectedclass=class_auth.connectedclass
    )
    enrollment_request.delete()

    return JsonResponse({})


#### FILE VIEWS ####
@login_required
def get_trend_chart(request: HttpRequest, classid: int) -> FileResponse:
    class_auth = auth_class(request, classid)

    if type(class_auth) not in ClassAuth.TEACHER_ADMIN:
        raise HttpRequest("Must be teacher to get trend chart")

    traitset = Traitset(class_auth.connectedclass.traitset)
    headers = (
        ["Time Stamp", "Population Size", "Net Merit $"]
        + [
            filter_text_to_default(f"<{x.uid}>", class_auth.connectedclass)
            for x in traitset.traits
        ]
        + [
            filter_text_to_default(f"ph: <{x.uid}>", class_auth.connectedclass)
            for x in traitset.traits
        ]
    )
    data = []
    for row in class_auth.connectedclass.trend_log:
        data.append(
            [
                row[models.Class.TIME_STAMP_KEY],
                row[models.Class.POPULATION_SIZE_KEY],
                row[models.Animal.DataKeys.NetMerit.value],
            ]
            + [row["genotype"][x.uid] for x in traitset.traits]
            + [row["phenotype"][x.uid] for x in traitset.traits]
        )

    return csv.create_csv_response("tendlog.csv", headers, data)


@login_required
def get_animal_chart(request: HttpRequest, classid: int) -> FileResponse:
    class_auth = auth_class(request, classid)

    if type(class_auth) not in ClassAuth.TEACHER_ADMIN:
        raise HttpRequest("Must be teacher to get animal chart")

    traitset = Traitset(class_auth.connectedclass.traitset)
    DataKeys = models.Animal.DataKeys

    headers = (
        [
            "Id",
            "Name",
            "Herd",
            "Class",
            "Generation",
            "Sex",
            "Sire",
            "Dam",
            "Inbreeding Percent",
            "Net Merit $",
        ]
        + [
            filter_text_to_default(f"<{x.uid}>", class_auth.connectedclass)
            for x in traitset.traits
        ]
        + [
            filter_text_to_default(f"ph: <{x.uid}>", class_auth.connectedclass)
            for x in traitset.traits
        ]
        + [
            filter_text_to_default(f"<{x.uid}>", class_auth.connectedclass)
            for x in traitset.recessives
        ]
    )
    data_row_order = (
        [
            DataKeys.Id,
            DataKeys.Name,
            DataKeys.HerdName,
            DataKeys.ClassName,
            DataKeys.Generation,
            DataKeys.Sex,
            DataKeys.SireId,
            DataKeys.DamId,
            DataKeys.InbreedingPercentage,
            DataKeys.NetMerit,
        ]
        + [(DataKeys.Genotype, x.uid) for x in traitset.traits]
        + [(DataKeys.Phenotype, x.uid) for x in traitset.traits]
        + [(DataKeys.NiceRecessives, x.uid) for x in traitset.recessives]
    )

    def data():
        for animal in (
            models.Animal.objects.select_related("herd", "connectedclass")
            .filter(connectedclass=class_auth.connectedclass)
            .iterator(chunk_size=255)
        ):
            row = []
            for key in data_row_order:
                value = animal.resolve_data_key(key, class_auth.connectedclass)
                if type(value) is str:
                    value = filter_text_to_default(value, class_auth.connectedclass)

                row.append(value)
            yield row

    return csv.create_csv_streaming_response("animal-chart.csv", headers, data())


#### JSON VIEWS ####
@login_required
def get_enrollments(request: HttpRequest, classid: int) -> JsonResponse:
    class_auth = auth_class(request, classid)

    if type(class_auth) not in ClassAuth.TEACHER_ADMIN:
        return Http404("Must be teacher to get_enrollments")

    json = {
        "enrollments": [
            x.json_dict()
            for x in models.Enrollment.objects.select_related("student").filter(
                connectedclass=class_auth.connectedclass
            )
        ],
        "enrollment_requests": [
            x.json_dict()
            for x in models.EnrollmentRequest.objects.select_related("student").filter(
                connectedclass=class_auth.connectedclass
            )
        ],
    }

    return JsonResponse(json)


@login_required
def get_herd(request: HttpRequest, classid: int, herdid: int) -> JsonResponse:
    class_auth = auth_class(request, classid, "class_herd", "starter_herd")
    herd_auth = auth_herd(class_auth, herdid)
    json = herd_auth.herd.json_dict()

    return JsonResponse(json)


@login_required
def get_assignments(request: HttpRequest, classid: int, herdid: int) -> JsonResponse:
    class_auth = auth_class(request, classid, "starter_herd", "class_herd")
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
