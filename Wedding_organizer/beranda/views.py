# beranda/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from pengguna.models import ProfilWO # <-- Import ProfilWO
from organizer.models import Paket
from organizer.models import Pesanan
from pengguna.models import ProfilWO
from django.db.models import Count, Q, Min

def index(request):
    profil_wos_unggulan = ProfilWO.objects.annotate(
        active_paket_count=Count('user__paket', filter=Q(user__paket__is_active=True)),
        # Mencari harga terendah dari paket yang aktif
        min_price=Min('user__paket__harga', filter=Q(user__paket__is_active=True))
    ).filter(
        active_paket_count__gt=0
    ).order_by('-user__date_joined')[:3]

    context = {
        'profil_wos_unggulan': profil_wos_unggulan,
    }
    return render(request, 'beranda/index.html', context)

@login_required
def daftar_wo_view(request):
    # Pastikan hanya customer yang bisa mengakses halaman ini
    if request.user.profil.role != 'customer':
        return redirect('dashboard_wo') # Jika WO, arahkan ke dashboard mereka

    # Ambil semua profil WO dari database
    profil_wos = ProfilWO.objects.annotate(
        active_paket_count=Count('user__paket', filter=Q(user__paket__is_active=True))
    ).filter(
        active_paket_count__gt=0
    ).order_by('nama_brand')

    context = {
        'profil_wos': profil_wos,
    }
    return render(request, 'beranda/daftar_wo.html', context)

@login_required
def detail_wo_view(request, wo_id):
    # Ambil profil WO berdasarkan ID user, atau tampilkan 404 jika tidak ada
    profil_wo = get_object_or_404(ProfilWO, user__id=wo_id)
    
    # Ambil semua paket yang aktif milik WO tersebut
    pakets = Paket.objects.filter(wo=profil_wo.user, is_active=True)

    context = {
        'profil_wo': profil_wo,
        'pakets': pakets,
    }
    return render(request, 'beranda/detail_wo.html', context)

@login_required
def detail_paket_view(request, paket_id):
    # Ambil paket berdasarkan ID, atau tampilkan halaman 404 jika tidak ada
    paket = get_object_or_404(Paket, id=paket_id)
    
    context = {
        'paket': paket,
    }
    return render(request, 'beranda/detail_paket.html', context)

@login_required
def status_pesanan_view(request):
    # Pastikan hanya customer yang bisa mengakses
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'customer':
        return redirect('index')

    # Ambil semua pesanan milik customer ini
    semua_pesanan = Pesanan.objects.filter(customer=request.user).order_by('-tgl_pesan')

    # Cari satu pesanan terbaru yang masih aktif
    pesanan_terbaru = semua_pesanan.filter(status__in=['menunggu', 'dikonfirmasi']).first()
    
    # Ambil sisa pesanan sebagai riwayat
    riwayat_pesanan = semua_pesanan.filter(status__in=['selesai', 'dibatalkan'])

    context = {
        'pesanan_terbaru': pesanan_terbaru,
        'riwayat_pesanan': riwayat_pesanan,
    }
    return render(request, 'beranda/status_pesanan.html', context)