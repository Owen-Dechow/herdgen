from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.homepage),
    path("auth/", include("django.contrib.auth.urls")),
    path("auth/signup", views.signup),
    path("auth/login/email", views.EmailLoginView.as_view()),
    path("auth/account", views.account),
    # Classes
    path("class/create", views.createclass),
    path("class/join", views.joinclass),
    path("class/requested", views.requestedclass),
    path("class/<int:classid>", views.openclass),
    path("class/<int:classid>/enrollments", views.enrollments),
    path(
        "class/<int:classid>/enrollments/update",
        views.update_enrollment,
    ),
    path("class/<int:classid>/assignments", views.assignments),
    path("class/<int:classid>/assignments/<int:assignmentid>", views.openassignment),
    path(
        "class/<int:classid>/assignments/<int:assignmentid>/delete",
        views.delete_assignment,
    ),
    path("class/<int:classid>/delete", views.deleteclass),
    path("class/<int:classid>/get-trend-chart", views.get_trend_chart),
    path("class/<int:classid>/get-animal-chart", views.get_animal_chart),
    path("class/<int:classid>/get-enrollments", views.get_enrollments),
    path(
        "class/<int:classid>/enrollments/<int:enrollmentid>/remove",
        views.remove_enrollment,
    ),
    path(
        "class/<int:classid>/enrollments/requests/<int:requestid>/confirm",
        views.confirm_enrollment,
    ),
    path(
        "class/<int:classid>/enrollments/requests/<int:requestid>/deny",
        views.deny_enrollment,
    ),
    # Herds
    path("class/<int:classid>/herd/<int:herdid>", views.openherd),
    path("class/<int:classid>/herd/<int:herdid>/get", views.get_herd),
    path(
        "class/<int:classid>/herd/<int:herdid>/breed/get-validation",
        views.get_breeding_validation,
    ),
    path(
        "class/<int:classid>/herd/<int:herdid>/breed",
        views.breed_herd,
    ),
    path(
        "class/<int:classid>/herd/<int:herdid>/assignments/get", views.get_assignments
    ),
    path(
        "class/<int:classid>/herd/<int:herdid>/assignments/submit-animal/<int:animalid>",
        views.submit_animal,
    ),
]
