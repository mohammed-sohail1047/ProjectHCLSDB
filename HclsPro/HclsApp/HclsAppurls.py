from  . import views
from django.urls import path

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('activate_admin/<int:id>', views.activate_admin, name='activate_admin'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('add/', views.add, name='add'),
    path('add-operational-admin/', views.add_operational_admin, name='add_operational_admin'),
    path('manage/', views.manage, name='manage'),
    path('OAdashboard/', views.OAdashboard, name='OAdashboard'),
    path('OAprofile/', views.OAprofile, name='OAprofile'),
    path('doctoradd/', views.doctoradd, name='doctoradd'),
    path('doctormanage/', views.doctormanage, name='doctormanage'),
    path('helperadd/', views.helperadd, name='helperadd'),  
    path('helpermanage/', views.helpermanage, name='helpermanage'),
    path('receptionistadd/', views.receptionistadd, name='receptionistadd'),
    path('receptionistmanage/', views.receptionistmanage, name='receptionistmanage'),
]