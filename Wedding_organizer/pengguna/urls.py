# pengguna/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .forms import LoginForm

urlpatterns = [
    path('registrasi/', views.registrasi_view, name='registrasi'),
    path('login/', auth_views.LoginView.as_view(template_name='pengguna/login.html', authentication_form=LoginForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='pengguna/logout.html'), name='logout'),
    path('buat-profil-wo/', views.buat_profil_wo_view, name='buat_profil_wo'),
    path('redirect-after-login/', views.redirect_after_login_view, name='redirect_after_login'),
    path('dashboard-wo/', views.dashboard_wo_view, name='dashboard_wo'),
    path('edit-profil-wo/', views.edit_profil_wo_view, name='edit_profil_wo'),
    path('edit-profil/', views.edit_profil_customer_view, name='edit_profil_customer'),



]