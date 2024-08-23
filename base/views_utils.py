from . import models
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpRequest


class ClassAuth:
    class Teacher:
        connectedclass: models.Class

        def __init__(self, connectedclass: models.Class):
            self.connectedclass = connectedclass

    class Student:
        enrollment: models.Enrollment
        connectedclass: models.Class

        def __init__(self, enrollment: models.Enrollment):
            self.enrollment = enrollment
            self.connectedclass = enrollment.connectedclass


def auth_class(
    request: HttpRequest, classid: int, *related: str
) -> ClassAuth.Teacher | ClassAuth.Student:
    connectedclass = get_object_or_404(
        models.Class.objects.select_related("teacher", *related), id=classid
    )

    if connectedclass.teacher == request.user:
        return ClassAuth.Teacher(connectedclass)
    else:
        return ClassAuth.Student(
            get_object_or_404(
                models.Enrollment.objects.select_related(
                    *["connectedclass__" + x for x in related]
                ),
                connectedclass=connectedclass,
                student=request.user,
            )
        )


class HerdAuth:
    class ClassHerd:
        def __init__(self, herd: models.Herd):
            self.herd = herd

    class StarterHerd:
        def __init__(self, herd: models.Herd):
            self.herd = herd

    class EnrollmentHerd:
        def __init__(self, herd: models.Herd):
            self.herd = herd

    class EnrollmentHerdAsTeacher:
        def __init__(self, herd: models.Herd):
            self.herd = herd


def auth_herd(
    class_auth: ClassAuth.Student | ClassAuth.Teacher, herdid: int, *related: str
) -> (
    HerdAuth.ClassHerd
    | HerdAuth.StarterHerd
    | HerdAuth.EnrollmentHerd
    | HerdAuth.EnrollmentHerdAsTeacher
):
    connectedclass = class_auth.connectedclass
    herd = get_object_or_404(
        models.Herd.objects.select_related(*related),
        id=herdid,
        connectedclass=connectedclass,
    )

    if connectedclass.class_herd == herd:
        return HerdAuth.ClassHerd(herd)
    elif connectedclass.starter_herd == herd:
        return HerdAuth.StarterHerd(herd)
    elif type(class_auth) is ClassAuth.Student and class_auth.enrollment.herd == herd:
        return HerdAuth.EnrollmentHerd(herd)
    elif type(class_auth) is ClassAuth.Teacher and herd.enrollment:
        return HerdAuth.EnrollmentHerdAsTeacher(herd)
    else:
        raise Http404("User does not have access to this herd")
