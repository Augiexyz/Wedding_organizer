import xendit
from xendit.apis import InvoiceApi
import json
import traceback
import requests
import base64
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Avg

# Import Forms
# PERBAIKAN: Pastikan UlasanForm diimpor
from .forms import GedungForm, PaketForm, PesananForm, UlasanForm

# Import Models
# PERBAIKAN: Pastikan Ulasan diimpor
from .models import Gedung, Paket, Pesanan, FotoPortofolio, FotoGedung, Ulasan

# ==========================================
# 1. DASHBOARD & ADMIN
# ==========================================
@login_required
def dashboard(request):
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo':
        return redirect('index')

    jumlah_paket = Paket.objects.filter(wo=request.user).count()
    jumlah_gedung = Gedung.objects.filter(wo=request.user).count()
    pesanan_baru = Pesanan.objects.filter(paket__wo=request.user, status='menunggu').count()
    
    pendapatan_total = 0
    pesanan_selesai = Pesanan.objects.filter(paket__wo=request.user, status='selesai')
    for p in pesanan_selesai:
        pendapatan_total += p.paket.harga

    chart_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun'] 
    chart_data = [0, 0, 0, 0, 0, int(pendapatan_total / 1000000)] 

    pesanan_terbaru = Pesanan.objects.filter(paket__wo=request.user).order_by('-tgl_pesan')[:5]
    paket_populer = Paket.objects.filter(wo=request.user)[:3]

    # Data Ulasan untuk Dashboard
    ulasan_list = Ulasan.objects.filter(wo=request.user).order_by('-created_at')
    rating_rata2 = ulasan_list.aggregate(Avg('rating'))['rating__avg'] or 0

    context = {
        'page_title': 'Dashboard WO',
        'jumlah_paket': jumlah_paket,
        'jumlah_gedung': jumlah_gedung,
        'pesanan_baru_count': pesanan_baru,
        'pesanan_selesai_count': pesanan_selesai.count(),
        'pendapatan_total': pendapatan_total,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'pesanan_terbaru': pesanan_terbaru,
        'paket_populer': paket_populer,
        'ulasan_list': ulasan_list,
        'rating_rata2': round(rating_rata2, 1),
    }
    return render(request, 'pengguna/dashboard_wo.html', context)


# ==========================================
# 2. MANAJEMEN GEDUNG
# ==========================================

@login_required
def kelola_gedung(request):
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo': return redirect('index')
    all_gedung = Gedung.objects.filter(wo=request.user).order_by('nama_gedung')
    return render(request, 'organizer/kelola_gedung.html', {'all_gedung': all_gedung, 'page_title': 'Kelola Gedung'})

@login_required
def tambah_gedung(request):
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo': return redirect('index')
    if request.method == 'POST':
        form = GedungForm(request.POST, request.FILES)
        if form.is_valid():
            gedung = form.save(commit=False)
            gedung.wo = request.user
            gedung.save()
            images = request.FILES.getlist('galeri_foto')
            for image in images:
                FotoGedung.objects.create(gedung=gedung, foto=image)
            messages.success(request, f"Gedung '{gedung.nama_gedung}' berhasil ditambahkan.")
            return redirect('kelola_gedung')
    else:
        form = GedungForm()
    return render(request, 'organizer/tambah_gedung.html', {'form': form, 'page_title': 'Tambah Gedung'})

@login_required
def edit_gedung(request, gedung_id):
    gedung = get_object_or_404(Gedung, id=gedung_id)
    if gedung.wo != request.user: return redirect('kelola_gedung')
    if request.method == 'POST':
        form = GedungForm(request.POST, request.FILES, instance=gedung)
        if form.is_valid():
            form.save()
            images = request.FILES.getlist('galeri_foto')
            for image in images:
                FotoGedung.objects.create(gedung=gedung, foto=image)
            messages.success(request, f"Gedung '{gedung.nama_gedung}' berhasil diperbarui.")
            return redirect('kelola_gedung')
    else:
        form = GedungForm(instance=gedung)
    return render(request, 'organizer/tambah_gedung.html', {'form': form, 'page_title': f'Edit Gedung: {gedung.nama_gedung}'})

@login_required
@require_POST
def hapus_gedung(request, gedung_id):
    gedung = get_object_or_404(Gedung, id=gedung_id)
    if gedung.wo != request.user: return redirect('kelola_gedung')
    gedung.delete()
    messages.success(request, f"Gedung '{gedung.nama_gedung}' berhasil dihapus.")
    return redirect('kelola_gedung')


# ==========================================
# 3. MANAJEMEN PAKET
# ==========================================

@login_required
def kelola_paket(request):
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo': return redirect('index')
    pakets = Paket.objects.filter(wo=request.user).order_by('nama_paket')
    return render(request, 'organizer/kelola_paket.html', {'pakets': pakets, 'page_title': 'Kelola Paket'})

@login_required 
def buat_paket_view(request):
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo': return redirect('index')
    if request.method == 'POST':
        form = PaketForm(request.POST, request.FILES)
        if form.is_valid():
            paket = form.save(commit=False)
            paket.wo = request.user
            paket.save()
            messages.success(request, f"Paket '{paket.nama_paket}' berhasil dibuat.")
            return redirect('kelola_paket')
    else:
        form = PaketForm()
    return render(request, 'organizer/buat_paket.html', {'form': form, 'page_title': 'Buat Paket'})

@login_required
def edit_paket_view(request, paket_id):
    paket = get_object_or_404(Paket, id=paket_id)
    if paket.wo != request.user: return redirect('kelola_paket')
    if request.method == 'POST':
        form = PaketForm(request.POST, request.FILES, instance=paket)
        if form.is_valid():
            form.save()
            messages.success(request, f"Paket '{paket.nama_paket}' berhasil diperbarui.")
            return redirect('kelola_paket')
    else:
        form = PaketForm(instance=paket)
    return render(request, 'organizer/buat_paket.html', {'form': form, 'page_title': f'Edit Paket: {paket.nama_paket}'})

@login_required
@require_POST
def hapus_paket_view(request, paket_id):
    paket = get_object_or_404(Paket, id=paket_id)
    if paket.wo != request.user: return redirect('kelola_paket')
    paket.delete()
    messages.success(request, "Paket berhasil dihapus.")
    return redirect('kelola_paket')


# ==========================================
# 4. MANAJEMEN PESANAN (WO)
# ==========================================

@login_required
def kelola_pesanan_view(request):
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo': return redirect('index')
    semua_pesanan = Pesanan.objects.filter(paket__wo=request.user).order_by('-tgl_pesan')
    pesanan_aktif = semua_pesanan.filter(status__in=['menunggu', 'dikonfirmasi', 'disiapkan'])
    riwayat_pesanan = semua_pesanan.filter(status__in=['selesai', 'dibatalkan'])
    return render(request, 'organizer/kelola_pesanan.html', {'pesanan_aktif': pesanan_aktif, 'riwayat_pesanan': riwayat_pesanan, 'page_title': 'Kelola Pesanan'})

@login_required
def detail_pesanan_view(request, pesanan_id):
    pesanan = get_object_or_404(Pesanan, id=pesanan_id)
    if pesanan.paket.wo != request.user: return redirect('kelola_pesanan')
    if request.method == 'POST':
        aksi = request.POST.get('aksi')
        if aksi == 'terima':
            pesanan.status = 'dikonfirmasi'
            messages.success(request, f"Pesanan #{pesanan.id} berhasil dikonfirmasi.")
        elif aksi == 'tolak':
            pesanan.status = 'dibatalkan'
            pesanan.catatan_pembatalan = request.POST.get('alasan_tolak', '')
            messages.warning(request, f"Pesanan #{pesanan.id} telah ditolak.")
        elif aksi == 'siapkan':
            if pesanan.status_pembayaran == 'lunas':
                pesanan.status = 'disiapkan'
                messages.success(request, "Status diperbarui: Sedang Disiapkan.")
                pesanan.save()
                return redirect('detail_pesanan', pesanan_id=pesanan.id)
            else:
                messages.error(request, "Gagal: Belum lunas.")
        elif aksi == 'selesai':
            pesanan.status = 'selesai'
            messages.success(request, f"Selamat! Pesanan #{pesanan.id} telah selesai.")
        pesanan.save()
        return redirect('kelola_pesanan')
    return render(request, 'organizer/detail_pesanan.html', {'pesanan': pesanan, 'page_title': f'Detail Pesanan #{pesanan.id}'})

# ==========================================
# 5. SISI CUSTOMER (ORDER & PAY - XENDIT DIRECT API)
# ==========================================
@login_required
def buat_pesanan_view(request, paket_id):
    paket = get_object_or_404(Paket, id=paket_id)
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'customer': return redirect('detail_paket', paket_id=paket.id)
    if request.method == 'POST':
        form = PesananForm(request.POST, paket=paket)
        if form.is_valid():
            pesanan = form.save(commit=False)
            pesanan.paket = paket
            pesanan.customer = request.user
            pesanan.status = 'menunggu'
            pesanan.save()
            messages.success(request, "Pesanan terkirim!")
            return redirect('pesanan_berhasil', pesanan_id=pesanan.id)
    else:
        form = PesananForm(paket=paket)
    return render(request, 'organizer/buat_pesanan.html', {'form': form, 'paket': paket, 'page_title': 'Buat Pesanan'})

@login_required
def pesanan_berhasil_view(request, pesanan_id):
    pesanan = get_object_or_404(Pesanan, id=pesanan_id)
    if pesanan.customer != request.user: return redirect('index')
    return render(request, 'organizer/pesanan_berhasil.html', {'pesanan': pesanan})

@login_required
def batalkan_pesanan_view(request, pesanan_id):
    pesanan = get_object_or_404(Pesanan, id=pesanan_id)
    if pesanan.customer != request.user: return redirect('status_pesanan')
    if request.method == 'POST' and pesanan.status == 'menunggu':
        pesanan.status = 'dibatalkan'
        pesanan.save()
    return redirect('status_pesanan')

@login_required
def halaman_pembayaran_view(request, pesanan_id):
    """
    MEMBUAT INVOICE XENDIT - DIRECT API (REQUESTS)
    """
    pesanan = get_object_or_404(Pesanan, id=pesanan_id)
    if pesanan.customer != request.user: return redirect('index')
    if pesanan.status_pembayaran == 'lunas': return redirect('status_pesanan')
    
    biaya_layanan = 5000
    total_pembayaran = int(pesanan.paket.harga + biaya_layanan)

    if request.method == 'POST':
        try:
            url = "https://api.xendit.co/v2/invoices"
            api_key = settings.XENDIT_SECRET_KEY
            auth_string = f"{api_key}:"
            auth_header = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
            
            headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/json"
            }

            external_id = f"ORDER-{pesanan.id}-{int(timezone.now().timestamp())}"
            # URL Ngrok (GANTI SESUAI TERMINAL ANDA)
            BASE_URL = "https://prevocalically-trivial-archimedes.ngrok-free.dev" 
            
            payload = {
                "external_id": external_id,
                "amount": total_pembayaran,
                "description": f"Pembayaran {pesanan.paket.nama_paket}",
                "payer_email": request.user.email if request.user.email else "customer@wokita.com",
                "customer": {
                    "given_names": pesanan.nama_pasangan or "Pelanggan",
                    "mobile_number": pesanan.telepon or "08123456789"
                },
                "success_redirect_url": f"{BASE_URL}/organizer/pesanan-berhasil/{pesanan.id}/",
                "failure_redirect_url": f"{BASE_URL}/organizer/pembayaran/{pesanan.id}/"
            }

            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200 or response.status_code == 201:
                response_data = response.json()
                return redirect(response_data['invoice_url'])
            else:
                print("Xendit Error:", response.text)
                messages.error(request, f"Gagal membuat invoice: {response.text}")
                return redirect('status_pesanan')

        except Exception as e:
            traceback.print_exc()
            messages.error(request, f"System Error: {e}")
            return redirect('status_pesanan')

    context = {'pesanan': pesanan, 'biaya_layanan': biaya_layanan, 'total_pembayaran': total_pembayaran}
    return render(request, 'organizer/pembayaran.html', context)


@csrf_exempt
def xendit_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            status = data.get('status')
            external_id = data.get('external_id')
            if status == 'PAID':
                pesanan_id = external_id.split('-')[1]
                pesanan = Pesanan.objects.get(id=pesanan_id)
                if pesanan.status_pembayaran != 'lunas':
                    pesanan.status_pembayaran = 'lunas'
                    pesanan.save()
                    print(f"✅ WEBHOOK: Pesanan #{pesanan_id} LUNAS!")
            return HttpResponse(status=200)
        except Exception:
            return HttpResponse(status=400)
    return HttpResponse(status=405)


# ==========================================
# 6. FITUR ULASAN (BARU)
# ==========================================

@login_required
def beri_ulasan_view(request, pesanan_id):
    """
    View untuk Customer memberikan ulasan setelah pesanan selesai.
    """
    pesanan = get_object_or_404(Pesanan, id=pesanan_id)

    # 1. Validasi Pemilik Pesanan
    if pesanan.customer != request.user:
        messages.error(request, "Anda tidak memiliki akses ke pesanan ini.")
        return redirect('index')

    # 2. Validasi Status Pesanan (Harus Selesai)
    if pesanan.status != 'selesai':
        messages.error(request, "Anda baru bisa memberikan ulasan setelah pesanan selesai.")
        return redirect('status_pesanan')

    # 3. Proses Form
    if request.method == 'POST':
        form = UlasanForm(request.POST)
        if form.is_valid():
            ulasan = form.save(commit=False)
            ulasan.wo = pesanan.paket.wo # Ulasan ditujukan ke WO ini
            ulasan.penulis = request.user
            ulasan.save()
            messages.success(request, "Terima kasih! Ulasan Anda berhasil dikirim.")
            return redirect('detail_wo', wo_id=pesanan.paket.wo.id) # Arahkan ke profil WO
    else:
        form = UlasanForm()

    context = {
        'form': form,
        'pesanan': pesanan,
        'page_title': 'Beri Ulasan'
    }
    return render(request, 'organizer/beri_ulasan.html', context)