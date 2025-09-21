# beranda/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('daftar-wo/', views.daftar_wo_view, name='daftar_wo'),
    
    path('wedding-organizer/<int:wo_id>/', views.detail_wo_view, name='detail_wo'),
    path('paket/<int:paket_id>/', views.detail_paket_view, name='detail_paket'),
    
    path('status-pesanan/', views.status_pesanan_view, name='status_pesanan'),

]