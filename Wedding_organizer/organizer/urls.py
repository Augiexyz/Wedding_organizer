# organizer/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('kelola-pesanan/', views.kelola_pesanan_view, name='kelola_pesanan'),
    path('pesanan/<int:pesanan_id>/', views.detail_pesanan_view, name='detail_pesanan'),
    
    path('kelola-paket/', views.kelola_paket_view, name='kelola_paket'),
    path('buat-paket/', views.buat_paket_view, name='buat_paket'),
    
    path('buat-pesanan/<int:paket_id>/', views.buat_pesanan_view, name='buat_pesanan'),
    
    path('pesanan-berhasil/<int:pesanan_id>/', views.pesanan_berhasil_view, name='pesanan_berhasil'),
    
    path('edit-paket/<int:paket_id>/', views.edit_paket_view, name='edit_paket'),
    
    path('pesanan-berhasil/<int:pesanan_id>/', views.pesanan_berhasil_view, name='pesanan_berhasil'),


    path('batalkan-pesanan/<int:pesanan_id>/', views.batalkan_pesanan_view, name='batalkan_pesanan'),
    
    path('pembayaran/<int:pesanan_id>/', views.halaman_pembayaran_view, name='halaman_pembayaran'),
    
    path('hapus-paket/<int:paket_id>/', views.hapus_paket_view, name='hapus_paket'),



]