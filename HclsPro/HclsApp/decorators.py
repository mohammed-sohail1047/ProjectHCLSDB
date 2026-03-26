from django.shortcuts import redirect
from functools import wraps


def normalize_admin_type(admin_type):
    """Convert admin_type to standard format (handles both int and string)"""
    if admin_type is None:
        return None
    
    admin_type_str = str(admin_type).strip().upper()
    
    # Handle database values
    if admin_type_str == "MADMIN" or admin_type_str == "1" or admin_type_str == "MANAGER ADMIN":
        return "MADMIN"
    elif admin_type_str == "OPADMIN" or admin_type_str == "2" or admin_type_str == "OPERATOR ADMIN":
        return "OPADMIN"
    
    return admin_type  # Return original if doesn't match


def login_required(view_func):
    """Decorator to check if user is logged in"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'admin_id' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def already_authenticated(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'admin_id' in request.session:
            admin_type = normalize_admin_type(request.session.get('admin_type'))
            
            if admin_type == "OPADMIN":
                return redirect('OAdashboard')
            elif admin_type == "MADMIN":
                return redirect('dashboard')
            else:
                # Clear corrupted session
                request.session.flush()
                return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def mAdmin_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if 'admin_id' not in request.session:
            return redirect('login')

        admin_type = normalize_admin_type(request.session.get('admin_type'))
        
        if admin_type != "MADMIN":
            # If they're an OpAdmin, redirect to their dashboard
            if admin_type == "OPADMIN":
                return redirect('OAdashboard')
            # Otherwise, logout and redirect to login
            request.session.flush()
            return redirect('login')

        return view_func(request, *args, **kwargs)

    return wrapper


def opAdmin_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if 'admin_id' not in request.session:
            return redirect('login')

        admin_type = normalize_admin_type(request.session.get('admin_type'))
        
        if admin_type != "OPADMIN":
            # If they're an MAdmin, redirect to their dashboard
            if admin_type == "MADMIN":
                return redirect('dashboard')
            # Otherwise, logout and redirect to login
            request.session.flush()
            return redirect('login')

        return view_func(request, *args, **kwargs)

    return wrapper

