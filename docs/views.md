# base.views
## EmailLoginView
> None

### Bases
* django.contrib.auth.views.LoginView

### Fields
`template` builtins.str

### Methods
### Source
```python
class EmailLoginView(LoginView):
    authentication_form = forms.EmailAuthenticationForm
    template = "registration/login.html"

```

