from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Avg
from django.core.mail import send_mail 
from django.conf import settings 
import urllib.parse

# Import Forms
from .forms import GedungForm, PaketForm, PesananForm, UlasanForm, ChatForm

# Import Models
from .models import Gedung, Paket, Pesanan, FotoPortofolio, FotoGedung, Ulasan, ChatDiskusi

# ==========================================
# 1. DASHBOARD
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
        # Hitung total pendapatan (Paket + Gedung) untuk statistik
        total_per_pesanan = p.paket.harga
        if p.gedung_dipilih:
            total_per_pesanan += p.gedung_dipilih.harga_sewa
        pendapatan_total += total_per_pesanan

    chart_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun'] 
    chart_data = [0, 0, 0, 0, 0, int(pendapatan_total / 1000000)] 

    pesanan_terbaru = Pesanan.objects.filter(paket__wo=request.user).order_by('-tgl_pesan')[:5]
    paket_populer = Paket.objects.filter(wo=request.user)[:3]

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
    return render(request, 'organizer/buat_paket.html', {'form': form, 'page_title': 'Edit Paket'})

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
    
    # Logika Link WA (Dipertahankan)
    no_hp = pesanan.telepon
    wa_link = "#"
    if no_hp:
        no_hp = no_hp.replace(" ", "").replace("-", "")
        if no_hp.startswith("0"):
            no_hp = "62" + no_hp[1:]
        
        pesan_wa = f"Halo {pesanan.customer.first_name}, Pesanan #{pesanan.id} ({pesanan.paket.nama_paket}) telah kami konfirmasi.\n\n"
        pesan_wa += "Untuk pemilihan MENU CATERING, silakan cek highlight Instagram kami ya.\n"
        pesan_wa += f"👉 Instagram: @{pesanan.paket.wo.profilwo.nama_brand.replace(' ', '').lower()}\n\nTerima kasih!"
        
        pesan_encoded = urllib.parse.quote(pesan_wa)
        wa_link = f"https://wa.me/{no_hp}?text={pesan_encoded}"

    if request.method == 'POST':
        aksi = request.POST.get('aksi')
        
        # Update Jadwal & Email (Dipertahankan)
        if 'update_jadwal' in request.POST:
            tgl_fitting = request.POST.get('tgl_fitting')
            tgl_survey = request.POST.get('tgl_survey')
            
            updated = False
            if tgl_fitting:
                pesanan.tgl_fitting = tgl_fitting
                updated = True
            if tgl_survey:
                pesanan.tgl_survey = tgl_survey
                updated = True
            
            if updated:
                pesanan.save()
                messages.success(request, "Jadwal kegiatan berhasil diperbarui.")
                try:
                    subject = f"Update Jadwal Pernikahan - {pesanan.paket.nama_paket}"
                    msg_fitting = tgl_fitting if tgl_fitting else 'Belum ditentukan'
                    msg_survey = tgl_survey if tgl_survey else 'Belum ditentukan'
                    message = f"Halo {pesanan.customer.first_name},\nJadwal baru pesanan #{pesanan.id}:\n1. Fitting: {msg_fitting}\n2. Survey: {msg_survey}\nTerima kasih."
                    email_from = settings.DEFAULT_FROM_EMAIL
                    recipient_list = [pesanan.customer.email]
                    send_mail(subject, message, email_from, recipient_list)
                    messages.info(request, "Email notifikasi terkirim.")
                except Exception:
                    pass
            return redirect('detail_pesanan', pesanan_id=pesanan.id)

        # Logika Status
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

    context = {'pesanan': pesanan, 'page_title': f'Detail Pesanan #{pesanan.id}', 'wa_link': wa_link}
    return render(request, 'organizer/detail_pesanan.html', context)


# ==========================================
# 5. SISI CUSTOMER & PEMBAYARAN (MANUAL)
# ==========================================

@login_required
def buat_pesanan_view(request, paket_id):
    paket = get_object_or_404(Paket, id=paket_id)
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'customer':
        return redirect('detail_paket', paket_id=paket.id)

    if request.method == 'POST':
        form = PesananForm(request.POST, paket=paket)
        if form.is_valid():
            pesanan = form.save(commit=False)
            pesanan.paket = paket
            pesanan.customer = request.user
            pesanan.status = 'menunggu'
            pesanan.save()
            messages.success(request, "Pesanan berhasil dikirim! Menunggu konfirmasi WO.")
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
    PEMBAYARAN MANUAL (TRANSFER) - LOGIKA TOTAL DIPERBAIKI
    """
    pesanan = get_object_or_404(Pesanan, id=pesanan_id)
    if pesanan.customer != request.user: return redirect('index')
    if pesanan.status_pembayaran == 'lunas': return redirect('status_pesanan')
    
    biaya_layanan = 5000
    
    # --- LOGIKA HITUNG TOTAL YANG BENAR ---
    harga_paket = pesanan.paket.harga
    harga_gedung = 0
    
    # Tambahkan harga gedung JIKA pesanan memiliki gedung (tidak None)
    if pesanan.gedung_dipilih:
        harga_gedung = pesanan.gedung_dipilih.harga_sewa
        
    total_pembayaran = int(harga_paket + harga_gedung + biaya_layanan)
    # -------------------------------------

    if request.method == 'POST':
        # LOGIKA MANUAL: Langsung ubah jadi Lunas saat diklik
        pesanan.status_pembayaran = 'lunas'
        pesanan.save()
        messages.success(request, "Konfirmasi Berhasil! Pesanan Anda kini berstatus Lunas.")
        return redirect('status_pesanan')

    context = {
        'pesanan': pesanan, 
        'biaya_layanan': biaya_layanan, 
        'total_pembayaran': total_pembayaran,
        'harga_gedung': harga_gedung # Kirim ke template agar bisa ditampilkan
    }
    return render(request, 'organizer/pembayaran.html', context)


# ==========================================
# 6. FITUR ULASAN
# ==========================================

@login_required
def beri_ulasan_view(request, pesanan_id):
    pesanan = get_object_or_404(Pesanan, id=pesanan_id)
    if pesanan.customer != request.user:
        return redirect('index')
    if pesanan.status != 'selesai':
        return redirect('status_pesanan')
    if hasattr(pesanan, 'data_ulasan'):
        return redirect('status_pesanan')

    if request.method == 'POST':
        form = UlasanForm(request.POST)
        if form.is_valid():
            ulasan = form.save(commit=False)
            ulasan.wo = pesanan.paket.wo
            ulasan.penulis = request.user
            ulasan.pesanan = pesanan
            ulasan.save()
            messages.success(request, "Ulasan terkirim!")
            return redirect('status_pesanan')
    else:
        form = UlasanForm()
    return render(request, 'organizer/beri_ulasan.html', {'form': form, 'pesanan': pesanan, 'page_title': 'Beri Ulasan'})

@login_required
def ruang_diskusi_view(request, pesanan_id):
    pesanan = get_object_or_404(Pesanan, id=pesanan_id)

    # Validasi Keamanan: Hanya Pemilik Pesanan (Customer) dan WO yang boleh masuk
    is_customer = (request.user == pesanan.customer)
    is_wo = (request.user == pesanan.paket.wo)

    if not is_customer and not is_wo:
        messages.error(request, "Anda tidak memiliki akses ke ruang diskusi ini.")
        return redirect('index')

    # Ambil semua chat urut dari yang terlama ke terbaru
    chats = ChatDiskusi.objects.filter(pesanan=pesanan).order_by('waktu_kirim')

    if request.method == 'POST':
        form = ChatForm(request.POST)
        if form.is_valid():
            chat = form.save(commit=False)
            chat.pesanan = pesanan
            chat.pengirim = request.user
            chat.save()
            return redirect('ruang_diskusi', pesanan_id=pesanan.id)
    else:
        form = ChatForm()

    context = {
        'pesanan': pesanan,
        'chats': chats,
        'form': form,
        'page_title': f'Diskusi Pesanan #{pesanan.id}'
    }
    return render(request, 'organizer/ruang_diskusi.html', context)

@login_required
def validasi_pemesanan(paket_dipilih, tanggal_booking):
    """
    Fungsi ini mengecek apakah Paket atau Gedung tersedia 
    pada tanggal yang diinginkan customer.
    
    Return: (Boleh_Pesan: Boolean, Pesan_Error: String)
    """

    # --- SKENARIO 1: VALIDASI KUOTA JASA WO ---
    # Jika paket yang dipilih TIDAK termasuk gedung (Hanya Jasa WO)
    if paket_dipilih.kategori_gedung == 'non_gedung':
        
        # Hitung berapa banyak pesanan yang sudah diterima WO ini di tanggal tersebut
        jumlah_pesanan_wo = Pesanan.objects.filter(
            paket__wo = paket_dipilih.wo,       # Milik WO yang sama
            tgl_acara = tanggal_booking,        # Tanggal yang sama
            status__in = ['dikonfirmasi', 'disiapkan', 'selesai'] # Status aktif
        ).count()

        # Batasan: Maksimal 3 acara per hari untuk satu WO
        BATAS_KUOTA_HARIAN = 3 
        
        if jumlah_pesanan_wo >= BATAS_KUOTA_HARIAN:
            return False, "Maaf, kuota tim WO kami sudah penuh untuk tanggal tersebut."


    # --- SKENARIO 2: VALIDASI KETERSEDIAAN GEDUNG FISIK ---
    # Jika paket termasuk gedung (S/M/L)
    else:
        # Cari gedung spesifik yang dipilih customer di form
        # (Anggap kita sudah dapat ID gedungnya dari input user)
        gedung_target = input_user.gedung_dipilih 

        # Cek apakah gedung tersebut SUDAH ada yang booking di tanggal itu
        cek_bentrok = Pesanan.objects.filter(
            gedung_dipilih = gedung_target,     # Gedung yang sama
            tgl_acara = tanggal_booking,        # Tanggal yang sama
            status__in = ['dikonfirmasi', 'disiapkan', 'selesai'] # Status aktif
        ).exists()

        if cek_bentrok:
            return False, f"Maaf, Gedung '{gedung_target.nama_gedung}' sudah terpesan di tanggal tersebut."

    
    # --- HASIL AKHIR ---
    # Jika lolos semua pengecekan di atas
    return True, "Tanggal Tersedia! Silakan lanjut pembayaran."