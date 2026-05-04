from django.shortcuts import redirect
from functools import wraps


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.role not in roles:
                return redirect('dashboard:index')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator