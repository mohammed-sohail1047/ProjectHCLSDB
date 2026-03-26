from django.shortcuts import redirect, render
from HclsWebApi.models import CheckLogin, PasswordResetToken
from django.contrib import messages
from .decorators import login_required, mAdmin_only, opAdmin_only, already_authenticated, normalize_admin_type
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import uuid
# from .decorators import login_required, already_authenticated, mAdmin_only, opAdmin_only


# Create your views here.


@already_authenticated
def home(request):
    return render(request, 'Admin/Anonymous/home.html')

@already_authenticated
def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        phone = request.POST.get('phone', '')
        admin_type = (request.POST.get('admin_type'))

        if CheckLogin.objects.filter(email=email).exists():
            return render(request, 'Admin/Anonymous/register.html', {
                'error': 'Email already exists'
            })

        CheckLogin.objects.create(
            email=email,
            username=username,
            password=password,
            phone=phone,
            admin_type=admin_type
        )

        return render(request, 'Admin/Anonymous/login.html', {
            'success': 'Registration successful!'
        })

    return render(request, 'Admin/Anonymous/register.html')

        
    #     # Create AdminLogin record
    #     # Note: AdminType should be set based on your business logic (default to 1 for now)
    #     try:
    #         # Get the next available ID
    #         last_admin = AdminLogin.objects.order_by('-Id').first()
    #         next_id = (last_admin.Id + 1) if last_admin else 1
            
    #         AdminLogin.objects.create(
    #             Id=next_id,
    #             Name=username,
    #             Gender=gender,
    #             Password=password,
    #             Phone=phone,
    #             Email=email,
    #             Address=address,
    #             AdminType_id=1,  # Default AdminType ID
    #             Status=False
    #         )
    #         return render(request, 'Admin/Anonymous/login.html')
    #     except Exception as e:
    #         return render(request, 'Admin/Anonymous/register.html', {'error': str(e)})
    # return render(request, 'Admin/Anonymous/register.html')


@already_authenticated
def login(request):
    if request.method == "POST":
        email = request.POST.get('username')
        password = request.POST.get('password')

        user = CheckLogin.objects.filter(email=email).first()

        if user and user.check_password(password):
            # 🔥 redirect if not activated
            if not user.status:
                return redirect('activate_admin', id=user.id)

            normalized_type = normalize_admin_type(user.admin_type)

            if not normalized_type:
                return render(request, 'Admin/Anonymous/login.html', {
                    'error': 'Invalid admin type. Contact support.'
                })

            request.session['admin_id'] = user.id
            request.session['admin_type'] = normalized_type

            if normalized_type == "MADMIN":
                return redirect('dashboard')
            else:
                return redirect('OAdashboard')

        return render(request, 'Admin/Anonymous/login.html', {
            'error': 'Invalid credentials'
        })

    return render(request, 'Admin/Anonymous/login.html')

# def login(request):
#     if request.method == "POST":
#         email = request.POST.get('username')
#         password = request.POST.get('password')

#         user = CheckLogin.objects.filter(email=email, password=password).first()

#         if user and user.admin_type:
#             # ✅ Ensure status is True before setting session
#             if not user.status:
#                 return redirect('Admin/Anonymous/activate_admin.html',id=user.id)

#             # Normalize admin_type from database
#             normalized_type = normalize_admin_type(user.admin_type)
            
#             if not normalized_type:
#                 return render(request, 'Admin/Anonymous/login.html', {
#                     'error': 'Invalid admin type. Contact support.'
#                 })

#             request.session['admin_id'] = user.id
#             request.session['admin_type'] = normalized_type
#             request.session.modified = True

#             if normalized_type == "MADMIN":
#                 return redirect('dashboard')
#             elif normalized_type == "OPADMIN":
#                 return redirect('OAdashboard')

#         return render(request, 'Admin/Anonymous/login.html', {'error': 'Invalid credentials'})

#     return render(request, 'Admin/Anonymous/login.html')
# def login(request):

#     # 🚫 If already logged in → redirect
#     if request.session.get("admin_id"):
#         admin_type = request.session.get("admin_type")

#         if admin_type == "1":
#             return redirect("dashboard")
#         else:
#             return redirect("OAdashboard")

#     if request.method == "POST":
#         email = request.POST.get("username")
#         password = request.POST.get("password")

#         try:
#             admin = CheckLogin.objects.get(email=email, password=password)

#             # ❌ Not active → go to activation page
#             if not admin.status:
#                 return redirect("activate_admin", admin.id)

#             # ✅ Create session
#             request.session["admin_id"] = admin.id
#             request.session["admin_type"] = admin.admin_type

#             # 🎯 Redirect based on role
#             if admin.admin_type == "MAdmin":
#                 return redirect("dashboard")
#             else:
#                 return redirect("OAdashboard")

#         except CheckLogin.DoesNotExist:
#             return render(request, "Admin/Anonymous/login.html", {
#                 "error": "Invalid credentials"
#             })

#     return render(request, "Admin/Anonymous/login.html")

@already_authenticated
def activate_admin(request, id):
    admin = CheckLogin.objects.get(id=id)

    if request.method == "POST":
        password = request.POST.get("password")

        # Verify password using check_password method (compares with hashed password)
        if admin.check_password(password):
            admin.status = True
            admin.save()
            return redirect("login")

        else:
            return render(request, "Admin/Anonymous/activate_admin.html", {
                "admin": admin,
                "error": "Incorrect password"
            })

    return render(request, "Admin/Anonymous/activate_admin.html", {
        "admin": admin
    })

@mAdmin_only
def dashboard(request):

    # if not request.session.get("admin_id"):
    #     return redirect("login")

    # if request.session.get("admin_type") != "MAdmin":
    #     return redirect("login")

    return render(request, "Admin/MAdmin/dashboard.html")

@mAdmin_only
def profile(request):
    try:
        admin_id = request.session.get('admin_id')
        admin = CheckLogin.objects.get(id=admin_id)
        
        context = {
            'admin': admin,
            'admin_username': admin.username,
            'admin_email': admin.email,
        }
    except CheckLogin.DoesNotExist:
        request.session.flush()
        return redirect('login')
    
    return render(request, 'Admin/MAdmin/profile_new.html', context)


@login_required
@mAdmin_only
def add_operational_admin(request):
    """View for MAdmin to add new Operational Admins"""
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone = request.POST.get('phone', '')

        # Validate passwords match
        if password != confirm_password:
            return render(request, 'Admin/MAdmin/add.html', {
                'error': 'Passwords do not match in the Operational Admin form'
            })

        # Check if email already exists
        if CheckLogin.objects.filter(email=email).exists():
            return render(request, 'Admin/MAdmin/add.html', {
                'error': 'Email already exists. Please use a different email address.'
            })

        # Check if username already exists
        if CheckLogin.objects.filter(username=username).exists():
            return render(request, 'Admin/MAdmin/add.html', {
                'error': 'Username already exists. Please choose a different username.'
            })

        # Create new Operational Admin
        CheckLogin.objects.create(
            email=email,
            username=username,
            password=password,
            phone=phone,
            admin_type='2'  # Operational Admin
        )

        return render(request, 'Admin/MAdmin/add.html', {
            'success': 'Operational Admin created successfully! They will receive an activation email.'
        })

    return render(request, 'Admin/MAdmin/add.html')

@login_required
@mAdmin_only
def add(request):
    return render(request, 'Admin/MAdmin/add.html')

@login_required
@mAdmin_only
def manage(request):
    return render(request, 'Admin/MAdmin/manage.html')

@opAdmin_only
def OAdashboard(request):
    return render(request, "Admin/OpAdmin/dashboard.html")

@opAdmin_only
def OAprofile(request):
    context = {
        'admin_username': request.session.get('admin_username'),
        'admin_email': request.session.get('admin_email'),
    }
    return render(request, 'Admin/OpAdmin/profile.html', context)




@login_required
@opAdmin_only
def doctoradd(request):
    return render(request, 'Admin/OpAdmin/doctor/add.html')  

@login_required
@opAdmin_only
def doctormanage(request):
    return render(request, 'Admin/OpAdmin/doctor/manage.html')  

@login_required
@opAdmin_only
def helperadd(request):
    return render(request, 'Admin/OpAdmin/helper/add.html')  

@login_required
@opAdmin_only
def helpermanage(request):
    return render(request, 'Admin/OpAdmin/helper/manage.html')

@login_required
@opAdmin_only
def receptionistadd(request):
    return render(request, 'Admin/OpAdmin/receptionist/add.html')  

@login_required
@opAdmin_only
def receptionistmanage(request):
    return render(request, 'Admin/OpAdmin/receptionist/manage.html')


def logout(request):
    request.session.flush()
    return redirect("login")


@already_authenticated
def forgot_password(request):
    """Handle forgot password email request"""
    if request.method == 'POST':
        email = request.POST.get('email')

        user = CheckLogin.objects.filter(email=email).first()

        if user:
            # Delete old tokens for this email
            PasswordResetToken.objects.filter(email=email).delete()

            # Generate new reset token
            reset_token = PasswordResetToken.objects.create(email=email)

            # Create reset link
            reset_link = request.build_absolute_uri(f'/reset-password/{reset_token.token}/')

            # Send email with reset link
            try:
                send_mail(
                    subject='Password Reset Request - HCLSDB',
                    message=f"""
Hello,

We received a request to reset your password. Click the link below to create a new password:

{reset_link}

This link will expire in 24 hours.

If you didn't request a password reset, you can safely ignore this email.

Best regards,
HCLSDB Team
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending email: {str(e)}")

        # Always show success message for security (don't reveal if email exists)
        return render(request, 'Admin/Anonymous/forgot_password.html', {
            'email_sent': True
        })

    return render(request, 'Admin/Anonymous/forgot_password.html')


@already_authenticated
def reset_password(request, token):
    """Handle password reset"""
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
    except PasswordResetToken.DoesNotExist:
        return render(request, 'Admin/Anonymous/reset_password.html', {
            'error': 'Invalid or expired reset link. Please request a new one.'
        })

    # Check if token is valid
    if not reset_token.is_valid():
        return render(request, 'Admin/Anonymous/reset_password.html', {
            'error': 'This reset link has expired. Please request a new one.'
        })

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validate passwords
        if not password or not confirm_password:
            return render(request, 'Admin/Anonymous/reset_password.html', {
                'error': 'Please fill in all fields.',
                'token': token
            })

        if password != confirm_password:
            return render(request, 'Admin/Anonymous/reset_password.html', {
                'error': 'Passwords do not match.',
                'token': token
            })

        if len(password) < 8:
            return render(request, 'Admin/Anonymous/reset_password.html', {
                'error': 'Password must be at least 8 characters long.',
                'token': token
            })

        # Update user password
        try:
            user = CheckLogin.objects.get(email=reset_token.email)
            user.password = password  # Will be hashed by the save method
            user.save()

            # Mark token as used
            reset_token.is_used = True
            reset_token.save()

            return render(request, 'Admin/Anonymous/reset_password.html', {
                'success': True
            })
        except CheckLogin.DoesNotExist:
            return render(request, 'Admin/Anonymous/reset_password.html', {
                'error': 'User not found.',
                'token': token
            })

    return render(request, 'Admin/Anonymous/reset_password.html', {
        'token': token
    })
