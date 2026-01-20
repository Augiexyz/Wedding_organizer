from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Avg, Sum
from django.core.mail import send_mail 
from django.conf import settings 
import urllib.parse
import datetime

# Import Forms
from .forms import GedungForm, PaketForm, PesananForm, UlasanForm, ChatForm

# Import Models
from .models import Gedung, Paket, Pesanan, FotoPortofolio, FotoGedung, Ulasan, ChatDiskusi

# ==========================================
# FUNGSI BANTUAN (VALIDASI JADWAL)
# ==========================================

def cek_ketersediaan(wo_object, tanggal_acara, gedung_object=None):
    """
    Fungsi Validasi Jadwal (Skenario 2 - Dinamis):
    1. Status 'menunggu' langsung dianggap membooking (LOCK).
    2. Gedung: 1 Hari cuma bisa 1 Acara (Strict).
    3. Jasa WO: Mengikuti 'kapasitas_harian' yang diatur di Profil WO.
    """
    
    # Status pesanan yang dianggap "MENGISI KUOTA/LOCK"
    status_lock = ['menunggu', 'dikonfirmasi', 'disiapkan', 'selesai']

    # 1. VALIDASI PIHAK GEDUNG (Jika customer memilih gedung)
    if gedung_object:
        bentrok_gedung = Pesanan.objects.filter(
            gedung_dipilih=gedung_object,
            tgl_acara=tanggal_acara,
            status__in=status_lock
        ).exists()

        if bentrok_gedung:
            return False, f"Maaf, Gedung '{gedung_object.nama_gedung}' sedang dibooking orang lain pada tanggal {tanggal_acara}. Mohon pilih gedung lain atau tanggal berbeda."

    # 2. VALIDASI PIHAK WO (Kuota Harian Tim - DINAMIS)
    jumlah_acara_wo = Pesanan.objects.filter(
        paket__wo=wo_object,
        tgl_acara=tanggal_acara,
        status__in=status_lock
    ).count()

    # --- LOGIKA DINAMIS ---
    # Mengambil kapasitas dari database ProfilWO
    try:
        # Pastikan wo_object adalah user, dan akses profilwo-nya
        BATAS_TIM_WO = wo_object.profilwo.kapasitas_harian
    except AttributeError:
        # Fallback jika profil belum dibuat atau field belum ada
        BATAS_TIM_WO = 1 
    
    if jumlah_acara_wo >= BATAS_TIM_WO:
        return False, f"Maaf, Tim WO kami sudah penuh. Kuota harian kami ({BATAS_TIM_WO} acara) sudah terpenuhi di tanggal {tanggal_acara}. Mohon pilih hari lain."

    return True, "Jadwal Tersedia"


# ==========================================
# 1. DASHBOARD
# ==========================================

@login_required
def dashboard(request):
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo':
        return redirect('index')

    # Data Statistik Dasar
    jumlah_paket = Paket.objects.filter(wo=request.user).count()
    jumlah_gedung = Gedung.objects.filter(wo=request.user).count()
    pesanan_baru = Pesanan.objects.filter(paket__wo=request.user, status='menunggu').count()
    
    # Hitung Total Pendapatan Keseluruhan (Selesai)
    pendapatan_total = 0
    pesanan_selesai = Pesanan.objects.filter(paket__wo=request.user, status='selesai')
    for p in pesanan_selesai:
        total_per_pesanan = p.paket.harga
        if p.gedung_dipilih:
            total_per_pesanan += p.gedung_dipilih.harga_sewa
        pendapatan_total += total_per_pesanan

    # --- GRAFIK (CHART) DINAMIS ---
    tahun_ini = datetime.date.today().year
    chart_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Ags', 'Sep', 'Okt', 'Nov', 'Des']
    chart_data = []

    for bulan in range(1, 13):
        pesanan_bulan_ini = Pesanan.objects.filter(
            paket__wo=request.user, 
            status='selesai',
            tgl_pesan__year=tahun_ini,
            tgl_pesan__month=bulan
        )
        
        total_bulan = 0
        for p in pesanan_bulan_ini:
            total_bulan += p.paket.harga
            if p.gedung_dipilih:
                total_bulan += p.gedung_dipilih.harga_sewa
        
        # Masukkan ke data chart (dalam jutaan)
        chart_data.append(int(total_bulan / 1000000))

    # Data List
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
    
    # --- LOGIKA GENERATE LINK WA (MANUAL CLICK) ---
    wa_link_jadwal = "#"
    
    if pesanan.telepon:
        # 1. Format Nomor HP (08xx -> 628xx)
        no_hp = pesanan.telepon.replace(" ", "").replace("-", "")
        if no_hp.startswith("0"):
            no_hp = "62" + no_hp[1:]
        
        # 2. Siapkan Data Tanggal (Ambil dari database)
        tgl_fitting_str = pesanan.tgl_fitting.strftime('%d %B %Y %H:%M') if pesanan.tgl_fitting else 'Belum ditentukan'
        tgl_survey_str = pesanan.tgl_survey.strftime('%d %B %Y %H:%M') if pesanan.tgl_survey else 'Belum ditentukan'

        # 3. Buat Template Pesan
        pesan_wa = f"Halo Kak {pesanan.customer.first_name}, berikut update jadwal persiapan pernikahan Anda:\n\n"
        pesan_wa += f"👔 *Jadwal Fitting:* {tgl_fitting_str}\n"
        pesan_wa += f"📍 *Jadwal Survey:* {tgl_survey_str}\n\n"
        pesan_wa += "Mohon konfirmasinya ya kak. Terima kasih! 🙏"
        
        # 4. Encode pesan agar aman di URL (spasi jadi %20, dll)
        pesan_encoded = urllib.parse.quote(pesan_wa)
        
        # 5. Gabungkan jadi Link
        wa_link_jadwal = f"https://wa.me/{no_hp}?text={pesan_encoded}"
    # ----------------------------------------------------

    if request.method == 'POST':
        aksi = request.POST.get('aksi')
        
        # Update Jadwal
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
                messages.success(request, "Jadwal berhasil disimpan! Silakan klik tombol WA di bawah untuk mengirim notifikasi ke customer.")
                
                # --- TETAP KIRIM EMAIL (Opsional/Backup) ---
                try:
                    subject = f"Update Jadwal - {pesanan.paket.nama_paket}"
                    msg_fitting = tgl_fitting if tgl_fitting else 'Belum ditentukan'
                    msg_survey = tgl_survey if tgl_survey else 'Belum ditentukan'
                    email_msg = f"Halo {pesanan.customer.first_name},\nJadwal baru:\nFitting: {msg_fitting}\nSurvey: {msg_survey}"
                    send_mail(subject, email_msg, settings.DEFAULT_FROM_EMAIL, [pesanan.customer.email])
                except:
                    pass
                # -------------------------------------------

            return redirect('detail_pesanan', pesanan_id=pesanan.id)

        # ... (Logika Status terima/tolak/siapkan/selesai TETAP SAMA) ...
        if aksi == 'terima':
            pesanan.status = 'dikonfirmasi'
            messages.success(request, "Pesanan dikonfirmasi.")
        elif aksi == 'tolak':
            pesanan.status = 'dibatalkan'
            pesanan.catatan_pembatalan = request.POST.get('alasan_tolak', '')
            messages.warning(request, "Pesanan ditolak.")
        elif aksi == 'siapkan':
            if pesanan.status_pembayaran == 'lunas':
                pesanan.status = 'disiapkan'
                messages.success(request, "Status: Sedang Disiapkan.")
                pesanan.save()
                return redirect('detail_pesanan', pesanan_id=pesanan.id)
            else:
                messages.error(request, "Gagal: Belum lunas.")
        elif aksi == 'selesai':
            pesanan.status = 'selesai'
            messages.success(request, "Pesanan Selesai.")
        
        pesanan.save()
        return redirect('kelola_pesanan')

    # Kirim wa_link_jadwal ke template
    context = {
        'pesanan': pesanan, 
        'page_title': f'Detail Pesanan #{pesanan.id}', 
        'wa_link_jadwal': wa_link_jadwal 
    }
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
            # --- IMPLEMENTASI VALIDASI ANTI-BENTROK ---
            # 1. Ambil data dari form
            tgl_input = form.cleaned_data.get('tgl_acara')
            gedung_input = form.cleaned_data.get('gedung_dipilih') # Bisa None

            # 2. Panggil fungsi cek_ketersediaan (Skenario 2: Locking)
            boleh_pesan, pesan_notif = cek_ketersediaan(
                wo_object=paket.wo, 
                tanggal_acara=tgl_input, 
                gedung_object=gedung_input
            )

            # 3. Jika Validasi Gagal (Penuh/Bentrok)
            if not boleh_pesan:
                messages.error(request, pesan_notif)
                return render(request, 'organizer/buat_pesanan.html', {'form': form, 'paket': paket, 'page_title': 'Buat Pesanan'})

            # 4. Jika Validasi Lolos, Simpan Pesanan
            pesanan = form.save(commit=False)
            pesanan.paket = paket
            pesanan.customer = request.user
            pesanan.status = 'menunggu' # Status 'menunggu' sekarang sudah otomatis memblokir jadwal
            pesanan.save()
            
            messages.success(request, "Pesanan berhasil dikirim! Jadwal tanggal telah kami kunci untuk Anda menunggu konfirmasi admin.")
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
    PEMBAYARAN MANUAL (TRANSFER)
    """
    pesanan = get_object_or_404(Pesanan, id=pesanan_id)
    if pesanan.customer != request.user: return redirect('index')
    if pesanan.status_pembayaran == 'lunas': return redirect('status_pesanan')
    
    biaya_layanan = 5000
    
    # Logic Total
    harga_paket = pesanan.paket.harga
    harga_gedung = 0
    if pesanan.gedung_dipilih:
        harga_gedung = pesanan.gedung_dipilih.harga_sewa
        
    total_pembayaran = int(harga_paket + harga_gedung + biaya_layanan)

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
        'harga_gedung': harga_gedung
    }
    return render(request, 'organizer/pembayaran.html', context)


# ==========================================
# 6. FITUR ULASAN & CHAT
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

    # Validasi Akses
    is_customer = (request.user == pesanan.customer)
    is_wo = (request.user == pesanan.paket.wo)

    if not is_customer and not is_wo:
        messages.error(request, "Anda tidak memiliki akses ke ruang diskusi ini.")
        return redirect('index')

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