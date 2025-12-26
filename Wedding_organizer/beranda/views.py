from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from pengguna.models import ProfilWO
from organizer.models import Paket, Pesanan, Gedung, Ulasan
from organizer.forms import UlasanForm
from django.db.models import Count, Q, Min, Avg

def index(request):
    """
    Halaman utama (Landing Page) - PUBLIK
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

def daftar_wo_view(request):
    """
    Halaman daftar Wedding Organizer - PUBLIK
    """
    # Ambil semua WO yang punya setidaknya 1 paket aktif
    profil_wos = ProfilWO.objects.annotate(
        active_paket_count=Count('user__paket_wo', filter=Q(user__paket_wo__is_active=True)),
        jumlah_gedung=Count('user__gedung_wo')
    ).filter(active_paket_count__gt=0).order_by('nama_brand')

    # Logika Pencarian Nama WO
    query = request.GET.get('q')
    if query:
        profil_wos = profil_wos.filter(nama_brand__icontains=query)

    context = {'profil_wos': profil_wos, 'page_title': 'Partner Wedding Organizer Kami'}
    return render(request, 'beranda/daftar_wo.html', context)

def daftar_gedung_view(request):
    """
    Halaman daftar Gedung - PUBLIK
    """
    # Hanya tampilkan gedung yang punya pemilik (WO aktif)
    gedungs = Gedung.objects.filter(wo__isnull=False).order_by('-created_at')

    # Logika Pencarian
    query = request.GET.get('q')     # Cari Nama Gedung
    jalan = request.GET.get('jalan') # Cari Nama Jalan (Lokasi)
    lokasi_filter = request.GET.get('lokasi') # Filter Dropdown (jika masih dipakai)
    
    if query:
        gedungs = gedungs.filter(nama_gedung__icontains=query)
    
    # REVISI: Pencarian berdasarkan Nama Jalan / Alamat
    if jalan:
        gedungs = gedungs.filter(lokasi__icontains=jalan)
    
    if lokasi_filter and lokasi_filter != 'Filter Lokasi':
        gedungs = gedungs.filter(lokasi__icontains=lokasi_filter)

    context = {
        'gedungs': gedungs,
        'page_title': 'Daftar Gedung Rekomendasi',
    }
    return render(request, 'beranda/daftar_gedung.html', context)

def detail_wo_view(request, wo_id):
    """
    Halaman detail profil WO - PUBLIK
    """
    profil_wo = get_object_or_404(ProfilWO, user__id=wo_id)
    pakets = Paket.objects.filter(wo=profil_wo.user, is_active=True)
    gedungs = Gedung.objects.filter(wo=profil_wo.user).order_by('nama_gedung')

    # --- TAMBAHAN: ULASAN ---
    ulasan_list = Ulasan.objects.filter(wo=profil_wo.user).order_by('-created_at')
    avg_rating = ulasan_list.aggregate(Avg('rating'))['rating__avg'] or 0

    # Form Ulasan (Opsional jika ingin posting dari sini)
    if request.method == 'POST' and request.user.is_authenticated:
        form = UlasanForm(request.POST)
        if form.is_valid():
            ulasan = form.save(commit=False)
            ulasan.wo = profil_wo.user
            ulasan.penulis = request.user
            ulasan.save()
            messages.success(request, "Ulasan Anda berhasil dikirim.")
            return redirect('detail_wo', wo_id=wo_id)
    else:
        form = UlasanForm()

    context = {
        'profil_wo': profil_wo, 
        'pakets': pakets, 
        'gedungs': gedungs,
        'ulasan_list': ulasan_list,
        'avg_rating': round(avg_rating, 1),
        'ulasan_form': form,
    }
    return render(request, 'beranda/detail_wo.html', context)

def detail_paket_view(request, paket_id):
    """
    Halaman detail paket - PUBLIK
    """
    paket = get_object_or_404(Paket, id=paket_id)
    
    # --- TAMBAHAN: DATA RATING UNTUK PAKET ---
    # Mengambil ulasan milik WO penyedia paket ini
    ulasan_list = Ulasan.objects.filter(wo=paket.wo).order_by('-created_at')
    rating_rata2 = ulasan_list.aggregate(Avg('rating'))['rating__avg'] or 0

    context = {
        'paket': paket,
        'rating_rata2': round(rating_rata2, 1),
        'jumlah_ulasan': ulasan_list.count(),
        'ulasan_list': ulasan_list # Jika ingin menampilkan ulasan di detail paket juga
    }
    return render(request, 'beranda/detail_paket.html', context)

def detail_gedung_view(request, gedung_id):
    """
    Halaman detail gedung - PUBLIK
    """
    gedung = get_object_or_404(Gedung, id=gedung_id)
    context = {
        'gedung': gedung, 
        'page_title': f'Detail Gedung: {gedung.nama_gedung}'
    }
    return render(request, 'beranda/detail_gedung.html', context)

@login_required
def status_pesanan_view(request):
    """
    Halaman customer untuk melihat status pesanan - PRIVAT (BUTUH LOGIN)
    """
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'customer':
        return redirect('index')

    semua_pesanan = Pesanan.objects.filter(customer=request.user).order_by('-tgl_pesan')
    pesanan_terbaru = semua_pesanan.filter(status__in=['menunggu', 'dikonfirmasi', 'disiapkan']).first()
    riwayat_pesanan = semua_pesanan.filter(status__in=['selesai', 'dibatalkan'])

    context = {
        'pesanan_terbaru': pesanan_terbaru,
        'riwayat_pesanan': riwayat_pesanan,
    }
    return render(request, 'beranda/status_pesanan.html', context)