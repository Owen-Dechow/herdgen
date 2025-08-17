# base.views_utils
## ClassAuth
> None

### Bases
* builtins.object

### Fields
`__annotations__` builtins.dict

`TEACHER_ADMIN` builtins.list

`__dict__` builtins.getset_descriptor

`__weakref__` builtins.getset_descriptor

### Methods
### Source
```python
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

```

## HerdAuth
> None

### Bases
* builtins.object

### Fields
`__dict__` builtins.getset_descriptor

`__weakref__` builtins.getset_descriptor

### Methods
### Source
```python
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

```

