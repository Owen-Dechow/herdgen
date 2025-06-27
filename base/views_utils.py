from . import models
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpRequest
from background_task import background


class ClassAuth:
    class Teacher:
        connectedclass: models.Class

        def __init__(self, connectedclass: models.Class):
            self.connectedclass = connectedclass

    class Admin:
        connectedclass: models.Class

        def __init__(self, connectedclass: models.Class):
            self.connectedclass = connectedclass

    class Student:
        enrollment: models.Enrollment
        connectedclass: models.Class

        def __init__(self, enrollment: models.Enrollment):
            self.enrollment = enrollment
            self.connectedclass = enrollment.connectedclass

    TEACHER_ADMIN: list[type[Teacher] | type[Admin]] = [Teacher, Admin]


def auth_class(
    request: HttpRequest, classid: int, *related: str
) -> ClassAuth.Teacher | ClassAuth.Student | ClassAuth.Admin:
    connectedclass = get_object_or_404(
        models.Class.objects.select_related("teacher", *related).defer("trend_log"),
        id=classid,
    )

    if connectedclass.deleted:
        raise Http404("Class no longer exists.")

    if connectedclass.teacher == request.user:
        return ClassAuth.Teacher(connectedclass)
    else:
        try:
            return ClassAuth.Student(
                models.Enrollment.objects.select_related(
                    *["connectedclass__" + x for x in related]
                )
                .defer("connectedclass__trend_log")
                .get(
                    connectedclass=connectedclass,
                    student=request.user,
                )
            )
        except models.Enrollment.DoesNotExist:
            if request.user.is_superuser:
                return ClassAuth.Admin(connectedclass)
            else:
                raise Http404("Cannot authenticate user for class.")


class HerdAuth:
    class ClassHerd:
        def __init__(self, herd: models.Herd):
            self.herd = herd

    class EnrollmentHerd:
        def __init__(self, herd: models.Herd):
            self.herd = herd

    class EnrollmentHerdAsTeacher:
        def __init__(self, herd: models.Herd):
            self.herd = herd

    class Admin:
        def __init__(self, herd: models.Herd):
            self.herd = herd


def auth_herd(
    class_auth: ClassAuth.Student | ClassAuth.Teacher | ClassAuth.Admin,
    herdid: int,
    *related: str,
) -> (
    HerdAuth.ClassHerd
    | HerdAuth.EnrollmentHerd
    | HerdAuth.EnrollmentHerdAsTeacher
    | HerdAuth.Admin
):
    connectedclass = class_auth.connectedclass
    herd = get_object_or_404(
        models.Herd.objects.select_related("connectedclass", *related).defer(
            "connectedclass__trend_log"
        ),
        id=herdid,
        connectedclass=connectedclass,
    )

    if connectedclass.class_herd == herd:
        return HerdAuth.ClassHerd(herd)
    elif type(class_auth) is ClassAuth.Student and class_auth.enrollment.herd == herd:
        return HerdAuth.EnrollmentHerd(herd)
    elif type(class_auth) is ClassAuth.Teacher and herd.enrollment:
        return HerdAuth.EnrollmentHerdAsTeacher(herd)
    elif type(class_auth) is ClassAuth.Admin:
        return HerdAuth.Admin(herd)
    else:
        raise Http404("User does not have access to this herd")

@background(schedule=0)
def deleteclass_background(classid: int):
    models.Class.objects.get(id=classid).delete()
