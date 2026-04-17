from django.shortcuts import redirect, render
from HclsWebApi.models import (
    CheckLogin,
    PasswordResetToken,
    AdminLogin,
    AdminType,
    Patient,
    Doctor,
    Employee,
    Department,
    Receptionist,
    Helper,
)
from django.contrib import messages
from .decorators import login_required, mAdmin_only, opAdmin_only, already_authenticated, normalize_admin_type
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .repositories.django_admin_repository import DjangoAdminRepository
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

        repo = DjangoAdminRepository()
        new_check = repo.create_checklogin(email=email, username=username, password=password, phone=phone, admin_type=admin_type)
        try:
            repo.create_adminlogin_from_check(new_check)
        except Exception as e:
            print('Warning: failed to create AdminLogin record for new CheckLogin:', e)

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
    admins = CheckLogin.objects.select_related('created_by').all()
    today = timezone.localdate()

    current_admin_id = request.session.get('admin_id')
    opadmins = []
    active_count = 0
    inactive_count = 0

    for a in admins:
        if normalize_admin_type(a.admin_type) == 'OPADMIN':
            creator = getattr(a, 'created_by', None)
            # skip if this OpAdmin was not created by the current MAdmin
            if not current_admin_id or not creator or getattr(creator, 'id', None) != current_admin_id:
                continue

            if a.status:
                active_count += 1
            else:
                inactive_count += 1

            created_by_name = creator.username if getattr(creator, 'username', None) else (creator.email if creator else 'System')
            opadmins.append({
                'id': a.id,
                'name': a.username or a.email,
                'role': 'OpAdmin',
                'email': a.email,
                'phone': a.phone,
                'created_by': created_by_name,
                'created_on': getattr(a, 'created_on', None),
                'status': 'Active' if a.status else 'Inactive',
            })

    patient_count = Patient.objects.count()
    doctor_count = Doctor.objects.count()
    department_count = Department.objects.count()
    staff_count = Employee.objects.count() + Receptionist.objects.count() + Helper.objects.count()
    appointments_count = Patient.objects.filter(EntryDateandTime__date=today).count()
    admitted_count = Patient.objects.filter(IsAdmitted=True).count()
    discharged_count = Patient.objects.exclude(ExitDateandTime__isnull=True).count()
    total_opadmins = active_count + inactive_count
    activation_rate = round((active_count / total_opadmins) * 100) if total_opadmins else 0

    recent_patients = list(
        Patient.objects.select_related('DoctorID')
        .order_by('-EntryDateandTime')[:4]
    )
    recent_admins = CheckLogin.objects.filter(created_by_id=current_admin_id).order_by('-created_on')[:5]

    activity_feed = []
    for patient in recent_patients:
        activity_feed.append({
            'title': patient.Pname,
            'subtitle': f"Assigned to Dr. {patient.DoctorID.Dname}",
            'time': patient.EntryDateandTime,
            'state': 'Admitted' if patient.IsAdmitted else 'Checked in',
        })
    for admin in recent_admins:
        activity_feed.append({
            'title': admin.username or admin.email,
            'subtitle': 'Operational admin onboarded',
            'time': admin.created_on,
            'state': 'Active' if admin.status else 'Pending activation',
        })
    activity_feed = sorted(activity_feed, key=lambda item: item['time'], reverse=True)[:6]

    context = {
        'patients_count': patient_count,
        'doctors_count': doctor_count,
        'appointments_count': appointments_count,
        'staff_count': staff_count,
        'department_count': department_count,
        'admitted_count': admitted_count,
        'discharged_count': discharged_count,
        'activation_rate': activation_rate,
        'recent_activities': activity_feed,
        'opadmins': opadmins,
        'opadmin_active_count': active_count,
        'opadmin_inactive_count': inactive_count,
        'total_opadmins': total_opadmins,
        'focus_cards': [
            {
                'label': 'Capacity',
                'value': f'{admitted_count} admitted',
                'meta': f'{discharged_count} discharged',
                'tone': 'success',
            },
            {
                'label': 'Admin activation',
                'value': f'{activation_rate}%',
                'meta': f'{inactive_count} still pending',
                'tone': 'warning',
            },
            {
                'label': 'Departments',
                'value': department_count,
                'meta': f'{doctor_count} doctors mapped',
                'tone': 'info',
            },
        ],
    }

    return render(request, "Admin/MAdmin/dashboard.html", context)

@mAdmin_only
def profile(request):
    try:
        admin_id = request.session.get('admin_id')
        admin = CheckLogin.objects.get(id=admin_id)
        message = None

        # Handle POST from MAdmin profile edit form (save changes + avatar)
        if request.method == 'POST':
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            gender = request.POST.get('gender')
            avatar_file = request.FILES.get('avatar')

            print('MAdmin profile POST:', {'name': name, 'phone': phone, 'address': address, 'gender': gender, 'has_avatar': bool(avatar_file)})

            if name:
                admin.username = name
            if phone is not None:
                admin.phone = phone
            if address is not None:
                admin.address = address
            if gender is not None:
                admin.gender = gender
            if avatar_file:
                admin.avatar = avatar_file

            try:
                admin.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('profile')
            except Exception as e:
                print('Error saving MAdmin profile:', str(e))
                messages.error(request, f'Error saving profile: {e}')

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
        # attach creator from session (if available)
        creator = None
        creator_id = request.session.get('admin_id')
        if creator_id:
            creator = CheckLogin.objects.filter(id=creator_id).first()

        repo = DjangoAdminRepository()
        new_check = repo.create_checklogin(email=email, username=username, password=password, phone=phone, admin_type='2', created_by=creator)
        try:
            repo.create_adminlogin_from_check(new_check)
        except Exception as e:
            print('Warning: failed to create AdminLogin for OpAdmin:', e)

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
    # Show all Managerial and Operational admins to MAdmin users
    from django.core.paginator import Paginator

    # Fetch all potential admin records
    admins = CheckLogin.objects.all().order_by('-created_on')

    # scope: 'my' (only records created by current MAdmin) or 'all'
    scope = request.GET.get('scope', 'my')
    current_admin_id = request.session.get('admin_id')

    # Build items list containing only Operational Admins with requested columns
    items = []
    for a in admins:
        if normalize_admin_type(a.admin_type) == 'OPADMIN':
            creator = a.created_by
            # if scope is 'my', only include those created by current admin
            if scope == 'my' and current_admin_id:
                if not creator or getattr(creator, 'id', None) != current_admin_id:
                    continue

            created_by_name = creator.username if creator and getattr(creator, 'username', None) else (creator.email if creator else 'System')
            items.append({
                'id': a.id,
                'name': a.username or a.email,
                'role': 'OpAdmin',
                'email': a.email,
                'phone': a.phone,
                'created_by': created_by_name,
                'created_on': getattr(a, 'created_on', None),
                'status': 'Active' if a.status else 'Inactive',
            })

    # Paginate results (25 per page)
    paginator = Paginator(items, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'items': page_obj.object_list,
        'page_obj': page_obj,
        'scope': scope,
    }
    return render(request, 'Admin/MAdmin/manage.html', context)


@login_required
@mAdmin_only
def edit(request, id):
    """Edit view for Manage table rows."""
    try:
        admin = CheckLogin.objects.get(id=id)
    except CheckLogin.DoesNotExist:
        messages.error(request, 'Record not found.')
        return redirect('manage')

    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        phone = request.POST.get('phone')
        status = request.POST.get('status') == 'on'

        if email and email != admin.email and CheckLogin.objects.filter(email=email).exclude(id=id).exists():
            messages.error(request, 'Email already in use.')
        elif username and username != admin.username and CheckLogin.objects.filter(username=username).exclude(id=id).exists():
            messages.error(request, 'Username already in use.')
        else:
            admin.email = email
            admin.username = username
            admin.phone = phone
            admin.status = status
            admin.save()
            messages.success(request, 'Admin updated successfully.')
            return redirect('manage')

    return render(request, 'Admin/MAdmin/edit.html', {'admin': admin})

@login_required
@mAdmin_only
def delete_admin(request, id):
    if request.method == 'POST':
        try:
            admin = CheckLogin.objects.get(id=id)
            admin.delete()
            # Note: The database should ideally cascade delete AdminLogin, etc.
            messages.success(request, 'Admin deleted successfully.')
        except CheckLogin.DoesNotExist:
            messages.error(request, 'Record not found.')
    return redirect('manage')

@login_required
@mAdmin_only
def bulk_delete_admins(request):
    if request.method == 'POST':
        admin_ids = request.POST.getlist('admin_ids')
        if admin_ids:
            # Delete multiple admins
            deleted_count, _ = CheckLogin.objects.filter(id__in=admin_ids).delete()
            messages.success(request, f'Successfully deleted {deleted_count} record(s).')
        else:
            messages.warning(request, 'No records selected for deletion.')
    return redirect('manage')

@opAdmin_only
def OAdashboard(request):
    today = timezone.localdate()
    appointments_today = Patient.objects.filter(EntryDateandTime__date=today).count()
    admissions_pending = Patient.objects.filter(IsAdmitted=True, ExitDateandTime__isnull=True).count()
    lab_results_pending = max(Patient.objects.filter(IsAdmitted=True).count() - Patient.objects.exclude(Medication='').count(), 0)
    unread_messages = CheckLogin.objects.filter(status=False, created_by_id=request.session.get('admin_id')).count()

    recent_patients = Patient.objects.select_related('DoctorID').order_by('-EntryDateandTime')[:6]
    operations = []
    for patient in recent_patients:
        operations.append({
            'timestamp': patient.EntryDateandTime,
            'description': f'{patient.Pname} routed to {patient.DoctorID.Dname}',
            'source': 'Patient desk',
            'level': 'warning' if patient.IsAdmitted else 'info',
        })

    recent_opadmins = CheckLogin.objects.filter(created_by_id=request.session.get('admin_id')).order_by('-created_on')[:3]
    for admin in recent_opadmins:
        operations.append({
            'timestamp': admin.created_on,
            'description': f'{admin.username or admin.email} account reviewed',
            'source': 'Admin queue',
            'level': 'info' if admin.status else 'warning',
        })
    operations = sorted(operations, key=lambda item: item['timestamp'], reverse=True)[:7]

    chart_labels = []
    chart_data = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        chart_labels.append(day.strftime('%a'))
        chart_data.append(Patient.objects.filter(EntryDateandTime__date=day).count())

    context = {
        'appointments_today': appointments_today,
        'admissions_pending': admissions_pending,
        'lab_results_pending': lab_results_pending,
        'unread_messages': unread_messages,
        'operations': operations,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'care_summary': [
            {'label': 'Doctors available', 'value': Doctor.objects.count(), 'meta': 'Across all specialities'},
            {'label': 'Front desk staff', 'value': Receptionist.objects.count(), 'meta': 'Reception coverage'},
            {'label': 'Support helpers', 'value': Helper.objects.count(), 'meta': 'Ward assistance'},
        ],
    }
    return render(request, "Admin/OpAdmin/dashboard.html", context)

@opAdmin_only
def OAprofile(request):
    # Render Operational Admin profile including creator info
    admin_id = request.session.get('admin_id')
    try:
        admin = CheckLogin.objects.get(id=admin_id)
    except CheckLogin.DoesNotExist:
        request.session.flush()
        return redirect('login')
    message = None
    # handle profile update including avatar upload
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        gender = request.POST.get('gender')
        avatar_file = request.FILES.get('avatar')
        # Debug prints to help trace incoming data
        print('OAprofile POST data:', {'name': name, 'phone': phone, 'address': address, 'gender': gender, 'has_avatar': bool(avatar_file)})

        if name:
            admin.username = name
        if phone is not None:
            admin.phone = phone
        if address is not None:
            admin.address = address
        if gender is not None:
            admin.gender = gender
        if avatar_file:
            admin.avatar = avatar_file

        try:
            admin.save()
            # Use messages framework and PRG pattern to avoid double-post
            messages.success(request, 'Profile updated successfully.')
            return redirect('OAprofile')
        except Exception as e:
            # Log and show error message so we can diagnose upload/save problems
            print('Error saving OAprofile:', str(e))
            messages.error(request, f'Error saving profile: {e}')
            # fallthrough to render the page with error message

    creator = admin.created_by
    created_by_name = creator.username if creator and getattr(creator, 'username', None) else (creator.email if creator else 'System')
    created_on_str = admin.created_on.strftime('%Y-%m-%d %H:%M:%S') if getattr(admin, 'created_on', None) else ''

    context = {
        'admin': admin,
        'admin_username': admin.username,
        'admin_email': admin.email,
        'created_by_name': created_by_name,
        'created_on': created_on_str,
        'appointments_today': 0,
        'admissions_pending': 0,
        'unread_messages': 0,
        'recent_activities': [],
        'message': message,
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
