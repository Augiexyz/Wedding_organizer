from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from pengguna.models import ProfilWO
from organizer.models import Paket, Pesanan, Gedung 
from django.db.models import Count, Q, Min

def index(request):
    """
    Halaman utama (Landing Page).
    """
    profil_wos_unggulan = ProfilWO.objects.annotate(
        active_paket_count=Count('user__paket_wo', filter=Q(user__paket_wo__is_active=True)),
        min_price=Min('user__paket_wo__harga', filter=Q(user__paket_wo__is_active=True))
    ).filter(
        active_paket_count__gt=0
    ).order_by('-user__date_joined')[:3]

    context = {
        'profil_wos_unggulan': profil_wos_unggulan,
    }
    return render(request, 'beranda/index.html', context)

@login_required
def daftar_wo_view(request):
    """
    Halaman daftar Wedding Organizer dengan fitur pencarian.
    """
    if request.user.profil.role != 'customer':
        return redirect('dashboard_wo')

    # Ambil semua WO yang punya setidaknya 1 paket aktif
    profil_wos = ProfilWO.objects.annotate(
        active_paket_count=Count('user__paket_wo', filter=Q(user__paket_wo__is_active=True)),
        
        # --- TAMBAHAN BARU: Hitung Jumlah Gedung ---
        jumlah_gedung=Count('user__gedung_wo')
        # -------------------------------------------
        
    ).filter(
        active_paket_count__gt=0
    ).order_by('nama_brand')

    # Logika Pencarian
    query = request.GET.get('q')
    if query:
        profil_wos = profil_wos.filter(nama_brand__icontains=query)

    context = {
        'profil_wos': profil_wos,
        'page_title': 'Partner Wedding Organizer Kami',
    }
    return render(request, 'beranda/daftar_wo.html', context)

def daftar_gedung_view(request):
    """
    Halaman publik untuk menampilkan daftar semua gedung rekomendasi.
    """
    # PERBAIKAN DI SINI:
    # Filter 'wo__isnull=False' artinya: Hanya ambil gedung yang kolom WO-nya TIDAK KOSONG.
    gedungs = Gedung.objects.filter(wo__isnull=False).order_by('-created_at')

    # Logika Pencarian
    query = request.GET.get('q')
    lokasi = request.GET.get('lokasi')
    
    if query:
        gedungs = gedungs.filter(nama_gedung__icontains=query)
    
    if lokasi and lokasi != 'Filter Lokasi':
        gedungs = gedungs.filter(lokasi__icontains=lokasi)

    context = {
        'gedungs': gedungs,
        'page_title': 'Daftar Gedung Rekomendasi',
    }
    return render(request, 'beranda/daftar_gedung.html', context)


@login_required
def detail_wo_view(request, wo_id):
    """
    Halaman detail profil WO, paket-paketnya, DAN gedung-gedungnya.
    """
    profil_wo = get_object_or_404(ProfilWO, user__id=wo_id)
    
    # Ambil paket aktif
    pakets = Paket.objects.filter(wo=profil_wo.user, is_active=True)
    
    # --- TAMBAHAN BARU: Ambil gedung milik WO ini ---
    gedungs = Gedung.objects.filter(wo=profil_wo.user).order_by('nama_gedung')
    # ------------------------------------------------

    context = {
        'profil_wo': profil_wo,
        'pakets': pakets,
        'gedungs': gedungs, # Kirim ke template
    }
    return render(request, 'beranda/detail_wo.html', context)

@login_required
def detail_paket_view(request, paket_id):
    """
    Halaman detail satu paket spesifik.
    """
    paket = get_object_or_404(Paket, id=paket_id)
    
    context = {
        'paket': paket,
    }
    return render(request, 'beranda/detail_paket.html', context)

@login_required
def status_pesanan_view(request):
    """
    Halaman customer untuk melihat status pesanan mereka.
    """
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'customer':
        return redirect('index')

    semua_pesanan = Pesanan.objects.filter(customer=request.user).order_by('-tgl_pesan')
    pesanan_terbaru = semua_pesanan.filter(status__in=['menunggu', 'dikonfirmasi']).first()
    riwayat_pesanan = semua_pesanan.filter(status__in=['selesai', 'dibatalkan'])

    context = {
        'pesanan_terbaru': pesanan_terbaru,
        'riwayat_pesanan': riwayat_pesanan,
    }
    return render(request, 'beranda/status_pesanan.html', context)

def detail_gedung_view(request, gedung_id):
    """
    Halaman detail untuk satu gedung spesifik.
    """
    # Ambil data gedung berdasarkan ID, atau error 404 jika tidak ketemu
    gedung = get_object_or_404(Gedung, id=gedung_id)
    
    context = {
        'gedung': gedung,
        'page_title': f'Detail Gedung: {gedung.nama_gedung}',
    }
    return render(request, 'beranda/detail_gedung.html', context)