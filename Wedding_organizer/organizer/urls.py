from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # DASHBOARD & ADMIN WO
    # ==========================================
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Kelola Pesanan
    path('kelola-pesanan/', views.kelola_pesanan_view, name='kelola_pesanan'),
    path('pesanan/<int:pesanan_id>/', views.detail_pesanan_view, name='detail_pesanan'),

    # Kelola Paket
    # PERBAIKAN DI SINI: Menggunakan 'views.kelola_paket'
    path('kelola-paket/', views.kelola_paket, name='kelola_paket'),
    path('buat-paket/', views.buat_paket_view, name='buat_paket'), 
    path('edit-paket/<int:paket_id>/', views.edit_paket_view, name='edit_paket'),
    path('hapus-paket/<int:paket_id>/', views.hapus_paket_view, name='hapus_paket'),

    # Kelola Gedung
    path('kelola-gedung/', views.kelola_gedung, name='kelola_gedung'),
    path('tambah-gedung/', views.tambah_gedung, name='tambah_gedung'),
    path('edit-gedung/<int:gedung_id>/', views.edit_gedung, name='edit_gedung'),
    path('hapus-gedung/<int:gedung_id>/', views.hapus_gedung, name='hapus_gedung'),


    # ==========================================
    # SISI CUSTOMER (PEMESANAN & PEMBAYARAN)
    # ==========================================
    path('buat-pesanan/<int:paket_id>/', views.buat_pesanan_view, name='buat_pesanan'),
    path('pesanan-berhasil/<int:pesanan_id>/', views.pesanan_berhasil_view, name='pesanan_berhasil'),
    path('batalkan-pesanan/<int:pesanan_id>/', views.batalkan_pesanan_view, name='batalkan_pesanan'),
    
    # Halaman Pembayaran (Redirect ke Xendit)
    path('pembayaran/<int:pesanan_id>/', views.halaman_pembayaran_view, name='halaman_pembayaran'),

    # ==========================================
    # WEBHOOK XENDIT
    # ==========================================
    path('api/webhook/xendit/', views.xendit_webhook, name='xendit_webhook'),
]