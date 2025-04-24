from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied
from teacher.models import Teacher

class TeacherBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                # Check if user is in TEACHER group
                if user.groups.filter(name='TEACHER').exists():
                    # Check if teacher is approved
                    try:
                        teacher = Teacher.objects.get(user=user)
                        if teacher.status:
                            return user
                        else:
                            # Teacher not approved
                            return None
                    except Teacher.DoesNotExist:
                        return None
                else:
                    return None
            else:
                return None
        except User.DoesNotExist:
            return None
