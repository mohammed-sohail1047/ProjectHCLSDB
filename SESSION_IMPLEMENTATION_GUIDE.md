# Django Session Management Implementation Guide

## ✅ What Has Been Implemented

### 1. **Session Management**
   - Sessions are automatically created when users successfully login
   - Sessions store: admin_id, admin_email, admin_username, admin_type
   - Session expiry: 1 hour (configurable in `HclsApp/views.py`)

### 2. **Admin Type System**
   - **Type 1**: Managerial Admin (MAdmin) - redirects to `/dashboard/`
   - **Type 2**: Operational Admin (OpAdmin) - redirects to `/OAdashboard/`
   - Admin type is selected during registration

### 3. **Authentication Flow**
   ✓ **Login**: 
     - User enters email and password
     - If inactive: redirect to activation page
     - If active: create session and redirect to appropriate dashboard

   ✓ **Registration**: 
     - New admin selects their type (MAdmin or OpAdmin)
     - Account starts as inactive (needs activation)

   ✓ **Activation**: 
     - Admin needs to verify password to activate account

   ✓ **Logout**: 
     - Session is cleared and user is redirected to login page

### 4. **Access Control Decorators**
   - `@already_authenticated`: Redirects logged-in users away from login/register pages
   - `@login_required`: Protects dashboard and admin pages - unauthorised users redirected to login

### 5. **Database Migration**
   - Added `admin_type` field to CheckLogin model
   - Field type: IntegerField with choices (1=MAdmin, 2=OpAdmin)
   - Migration `0008_checklogin_admin_type.py` has been applied

---

## 🔧 Files Modified/Created

### Modified Files:
1. **HclsWebApi/models.py**
   - Added `admin_type` field to CheckLogin model with ADMIN_TYPE_CHOICES

2. **HclsApp/views.py**
   - Added session creation on successful login
   - Added logout view
   - Applied @login_required decorator to protected views
   - Applied @already_authenticated decorator to public pages
   - Session data passed to templates

3. **HclsApp/HclsAppurls.py**
   - Added logout URL route

4. **templates/Admin/Anonymous/login.html**
   - Fixed error message display (error vs errors)
   - Added success message display

5. **templates/Admin/Anonymous/register.html**
   - Added admin_type dropdown selection

### Created Files:
1. **HclsApp/decorators.py**
   - Contains `@login_required` and `@already_authenticated` decorators

2. **templates/Admin/logout_snippet.html**
   - Logout button template snippet for your dashboards

---

## 📝 How to Add Logout Button to Your Dashboards

Add this to your dashboard templates (MAdmin and OpAdmin):

```html
<!-- In your dashboard navbar/header -->
{% include 'Admin/logout_snippet.html' %}

<!-- Or use the simple button -->
<a href="{% url 'logout' %}" class="btn btn-danger btn-sm">Logout</a>
```

### Example for MAdmin Dashboard:
Edit `templates/Admin/MAdmin/dashboard.html`:

```html
{% extends 'Admin/MAdmin/base.html' %}
{% load static %}

{% block content %}
    <div class="navbar-end" style="float: right; margin: 10px;">
        <span>Welcome, {{ admin_username }}</span>
        <a href="{% url 'logout' %}" class="btn btn-danger btn-sm">Logout</a>
    </div>
    
    <!-- Your dashboard content -->
{% endblock %}
```

### Example for OpAdmin Dashboard:
Edit `templates/Admin/OpAdmin/dashboard.html`:

```html
{% extends 'Admin/OpAdmin/base.html' %}
{% load static %}

{% block content %}
    <div class="navbar-end" style="float: right; margin: 10px;">
        <span>Welcome, {{ admin_username }}</span>
        <a href="{% url 'logout' %}" class="btn btn-danger btn-sm">Logout</a>
    </div>
    
    <!-- Your dashboard content -->
{% endblock %}
```

---

## 🔒 Security Features

✓ **Session Security**:
   - Sessions expire after 1 hour (adjust in settings.py: `SESSION_COOKIE_AGE = 3600`)
   - Only authenticated users can access dashboards
   - Logged-in users cannot access login/register pages

✓ **Protected Routes**:
   - All dashboard paths require login
   - Public pages: home, login, register, activate_admin
   - Protected pages: dashboard, profile, add, manage, doctor operations, etc.

---

## 🚀 Testing the Implementation

### Test Case 1: Create New Account
1. Go to `/register/`
2. Fill form with:
   - Email: test@example.com
   - Username: testadmin
   - Phone: 1234567890 (optional)
   - Admin Type: Select "Managerial Admin" or "Operational Admin"
   - Password: secure_password123
3. Click "Create account"
4. Should be redirected to login page

### Test Case 2: Activate Account
1. Go to `/login/`
2. Enter email and password
3. Should be redirected to activation page (if status=False)
4. Confirm password and click activate
5. Should redirect back to login

### Test Case 3: Login Successfully
1. Go to `/login/`
2. Enter credentials
3. If admin_type=1 (MAdmin): redirect to `/dashboard/`
4. If admin_type=2 (OpAdmin): redirect to `/OAdashboard/`

### Test Case 4: Session Persistence
1. After login, navigate to other pages
2. Session data is preserved
3. Try accessing `/login/` - should redirect to dashboard

### Test Case 5: Logout
1. Click logout button on dashboard
2. Should be redirected to login page
3. Session should be cleared
4. Cannot access `/dashboard/` without logging in again

---

## ⚙️ Configuration

### To Change Session Expiry Time:
Edit `HclsApp/views.py` line in login view:
```python
request.session.set_expiry(3600)  # Change 3600 to desired seconds (e.g., 86400 for 24 hours)
```

### To Change Default Admin Type:
Edit `HclsWebApi/models.py`:
```python
admin_type = models.IntegerField(choices=ADMIN_TYPE_CHOICES, default=1)  # Change default value
```

### To Add More Admin Types:
1. Update ADMIN_TYPE_CHOICES in models.py
2. Run: `python manage.py makemigrations`
3. Update decorators.py `already_authenticated()` function
4. Update register.html form options

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Import decorators failed" | Ensure `decorators.py` exists in HclsApp folder |
| "Logout button not showing" | Add logout button to your dashboard templates |
| "Session not persisting" | Check Django SessionMiddleware is enabled in settings.py |
| "Redirect loop on login" | Verify @already_authenticated is on login view |
| "Cannot access dashboard" | Check @login_required decorator is applied |

---

## 📌 Important Notes

1. **Existing Data**: The admin_type field defaults to 1 for existing users
2. **Session Security**: In production, set `SESSION_COOKIE_SECURE = True` in settings.py
3. **HTTPS**: Always use HTTPS in production (sessions are more secure)
4. **Remember Me**: Currently not implemented (optional feature to add)

---

## 📚 Next Steps (Optional Enhancements)

1. **Add "Remember Me" checkbox**
2. **Implement password hashing** (currently using plain text - NOT recommended for production)
3. **Add email verification** for new registrations
4. **Implement role-based access control** (RBAC)
5. **Add password reset functionality**
6. **Session activity timeout** (auto-logout after inactivity)

---

**Implementation Status**: ✅ Complete
**Date**: March 18, 2026
**Requirements Met**: All session management requirements implemented
