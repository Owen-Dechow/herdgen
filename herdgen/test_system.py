from django.apps import apps

def test(condition=None):
    def decorator(*args, **kwargs):
        def wrapper(func):
            func._condition = condition
            return func(*args, **kwargs)

        return wrapper

    return decorator


class TestRunner:
    tests: list

    def __init__(self, *args, **kwargs):
        self.tests = []
        

        # for app in apps.get_app_configs():
        #     self.import_tests(app.name)

    def import_tests(self, mod):
        module = __import__(mod).tests_suite
        for a in module.__dict__:
            print(a)

    def run_tests(self, test_labels):
        print(self.tests)
