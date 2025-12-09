from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST 

# Import model dan form Anda
# Kita bersihkan sedikit impor yang berulang
from .models import Pesanan, Paket, Gedung, FotoPortofolio
from .forms import PaketForm, PesananForm, GedungForm

# --- VIEW DASHBOARD YANG HILANG ---
# Kita tambahkan view dashboard yang kita buat di percakapan sebelumnya
@login_required
def dashboard(request):
    # Pastikan hanya WO yang bisa akses
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo':
        return redirect('index') # Redirect ke index jika bukan WO

    # Ambil semua paket sebagai contoh
    all_pakets = Paket.objects.filter(wo=request.user)
    
    context = {
        'all_pakets': all_pakets,
        'page_title': 'Dashboard / Kelola Paket'
    }
    # Arahkan ke template kelola_paket untuk sementara
    return render(request, 'organizer/kelola_paket.html', context)

# --- VIEW ANDA YANG SUDAH ADA (DIMULAI DARI SINI) ---

@login_required
def kelola_pesanan_view(request):
    """
    Menampilkan daftar pesanan masuk dan riwayat pesanan untuk WO.
    """
    # Pastikan hanya WO yang akses
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo':
        return redirect('index')

    # Ambil pesanan yang terkait dengan PAKET milik WO ini
    # Kita filter berdasarkan paket__wo
    semua_pesanan = Pesanan.objects.filter(paket__wo=request.user).order_by('-tgl_pesan')

    # Pisahkan Pesanan Aktif (Menunggu / Dikonfirmasi)
    pesanan_aktif = semua_pesanan.filter(status__in=['menunggu', 'dikonfirmasi'])

    # Pisahkan Riwayat (Selesai / Dibatalkan)
    riwayat_pesanan = semua_pesanan.filter(status__in=['selesai', 'dibatalkan'])

    context = {
        'pesanan_aktif': pesanan_aktif,
        'riwayat_pesanan': riwayat_pesanan,
        'page_title': 'Kelola Pesanan Masuk'
    }
    return render(request, 'organizer/kelola_pesanan.html', context)

@login_required
def detail_pesanan_view(request, pesanan_id):
    """
    Logika detail pesanan untuk WO: Konfirmasi, Siapkan, Selesai.
    """
    pesanan = get_object_or_404(Pesanan, id=pesanan_id)

    if pesanan.paket.wo != request.user:
        messages.error(request, "Anda tidak memiliki akses ke pesanan ini.")
        return redirect('kelola_pesanan')

    if request.method == 'POST':
        aksi = request.POST.get('aksi')
        
        if aksi == 'terima':
            pesanan.status = 'dikonfirmasi'
            messages.success(request, f"Pesanan #{pesanan.id} berhasil dikonfirmasi. Menunggu pembayaran.")
        
        elif aksi == 'tolak':
            pesanan.status = 'dibatalkan'
            alasan = request.POST.get('alasan_tolak', '')
            pesanan.catatan_pembatalan = alasan
            messages.warning(request, f"Pesanan #{pesanan.id} telah ditolak.")
            
        # --- BAGIAN INI YANG MUNGKIN HILANG DI FILE ANDA ---
        elif aksi == 'siapkan':
            # Cek apakah sudah bayar
            if pesanan.status_pembayaran == 'lunas':
                pesanan.status = 'disiapkan'  # <--- INI KUNCINYA
                pesanan.save()                # <--- JANGAN LUPA SAVE
                messages.success(request, "Status diubah menjadi: Sedang Disiapkan.")
                # Redirect kembali ke halaman detail agar perubahan langsung terlihat
                return redirect('detail_pesanan', pesanan_id=pesanan.id)
            else:
                messages.error(request, "Gagal: Pelanggan belum melunasi pembayaran.")
                return redirect('detail_pesanan', pesanan_id=pesanan.id)
        # ---------------------------------------------------

        elif aksi == 'selesai':
            pesanan.status = 'selesai'
            messages.success(request, f"Pesanan #{pesanan.id} telah selesai.")

        pesanan.save()
        return redirect('kelola_pesanan')

    context = {
        'pesanan': pesanan,
        'page_title': f'Detail Pesanan #{pesanan.id}'
    }
    return render(request, 'organizer/detail_pesanan.html', context)

@login_required
def kelola_paket_view(request):
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo':
        return redirect('index')

    # Ambil semua paket milik WO yang sedang login
    pakets = Paket.objects.filter(wo=request.user).order_by('nama_paket')
    
    context = {
        'pakets': pakets,
    }
    return render(request, 'organizer/kelola_paket.html', context)

# --- PERBAIKAN: Menambahkan @ pada @login_required ---
@login_required 
def buat_paket_view(request):
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo':
        return redirect('index')

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
        # CATATAN: Kita SUDAH MENGHAPUS baris filter queryset 'gedung' 
        # karena sekarang pilihannya statis (S, M, L) di forms.py

    context = {
        'form': form,
        'page_title': 'Buat Paket Baru'
    }
    return render(request, 'organizer/buat_paket.html', context)


@login_required
def buat_pesanan_view(request, paket_id):
    """
    View untuk Customer membuat pesanan baru.
    """
    # 1. Ambil paket yang mau dipesan
    paket = get_object_or_404(Paket, id=paket_id)

    # 2. Cek apakah user adalah Customer
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'customer':
        messages.error(request, 'Maaf, hanya akun Customer yang bisa membuat pesanan.')
        return redirect('detail_paket', paket_id=paket.id)

    if request.method == 'POST':
        # 3. Saat Submit: Kirim 'paket' ke form agar validasi gedung berjalan
        form = PesananForm(request.POST, paket=paket)
        
        if form.is_valid():
            pesanan = form.save(commit=False)
            pesanan.paket = paket
            pesanan.customer = request.user
            
            # Status awal otomatis 'menunggu'
            pesanan.status = 'menunggu'
            pesanan.save()
            
            messages.success(request, "Pesanan Anda berhasil dikirim! Menunggu konfirmasi WO.")
            return redirect('pesanan_berhasil', pesanan_id=pesanan.id)
    else:
        # 4. Saat Buka Halaman: Kirim 'paket' ke form agar dropdown gedung terfilter
        form = PesananForm(paket=paket)

    context = {
        'form': form,
        'paket': paket,
        'page_title': f'Buat Pesanan: {paket.nama_paket}'
    }
    # Kita akan buat template ini di langkah selanjutnya
    return render(request, 'organizer/buat_pesanan.html', context)


@login_required
def pesanan_berhasil_view(request, pesanan_id):
    """
    Halaman sukses setelah memesan.
    """
    pesanan = get_object_or_404(Pesanan, id=pesanan_id)

    # Keamanan: Pastikan hanya pemesan yang bisa lihat
    if pesanan.customer != request.user:
        return redirect('index')

    context = {
        'pesanan': pesanan,
        'page_title': 'Pesanan Berhasil'
    }
    # Kita akan buat template ini nanti juga
    return render(request, 'organizer/pesanan_berhasil.html', context)

@login_required
def edit_paket_view(request, paket_id):
    paket = get_object_or_404(Paket, id=paket_id)
    
    if paket.wo != request.user:
        messages.error(request, "Anda tidak memiliki izin mengedit paket ini.")
        return redirect('kelola_paket')

    if request.method == 'POST':
        form = PaketForm(request.POST, request.FILES, instance=paket)
        if form.is_valid():
            form.save()
            messages.success(request, f"Paket '{paket.nama_paket}' berhasil diperbarui.")
            return redirect('kelola_paket')
    else:
        form = PaketForm(instance=paket)
        # CATATAN: Kita juga menghapus filter queryset di sini

    context = {
        'form': form,
        'paket': paket,
        'page_title': f'Edit Paket: {paket.nama_paket}'
    }
    # Kita gunakan template buat_paket.html untuk edit juga (reusable)
    return render(request, 'organizer/buat_paket.html', context)

@login_required
def batalkan_pesanan_view(request, pesanan_id):
    pesanan = get_object_or_404(Pesanan, id=pesanan_id)

    # Keamanan: Pastikan hanya customer pemilik pesanan yang bisa membatalkan
    if pesanan.customer != request.user:
        messages.error(request, "Anda tidak memiliki izin untuk membatalkan pesanan ini.")
        return redirect('status_pesanan')

    # Logika: Pastikan hanya pesanan yang statusnya "Menunggu Konfirmasi" yang bisa dibatalkan
    if pesanan.status != 'menunggu':
        messages.warning(request, "Pesanan ini sudah tidak dapat dibatalkan.")
        return redirect('status_pesanan')

    # Hanya proses pembatalan jika metodenya POST (dari form di pop-up)
    if request.method == 'POST':
        pesanan.status = 'dibatalkan'
        pesanan.save()
        messages.success(request, f"Pesanan #{pesanan.id} telah berhasil dibatalkan.")
        return redirect('status_pesanan')

    # Jika diakses secara tidak sengaja (bukan via POST), kembalikan saja
    return redirect('status_pesanan')

@login_required
def halaman_pembayaran_view(request, pesanan_id):
    pesanan = get_object_or_404(Pesanan, id=pesanan_id)

    # Keamanan: Pastikan hanya customer pemilik pesanan yang bisa membayar
    if pesanan.customer != request.user:
        messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini.")
        return redirect('status_pesanan')

    if request.method == 'POST':
        # --- PERBAIKAN PENTING ADA DI SINI ---
        # 1. Ubah status pembayaran menjadi 'lunas'
        pesanan.status_pembayaran = 'lunas'

        # 2. Kita juga bisa mengubah status pesanan menjadi 'selesai'
        #    jika pembayaran adalah langkah terakhir dalam alur.
        #    Untuk sekarang kita biarkan agar WO yang menandai selesai.
        # pesanan.status = 'selesai' 

        pesanan.save() # Simpan perubahan ke database

        messages.success(request, f"Pembayaran untuk pesanan #{pesanan.id} berhasil! Terima kasih.")
        return redirect('status_pesanan')

    # Logika untuk menampilkan halaman (tetap sama)
    biaya_layanan = 500000 
    total_pembayaran = pesanan.paket.harga + biaya_layanan

    context = {
        'pesanan': pesanan,
        'biaya_layanan': biaya_layanan,
        'total_pembayaran': total_pembayaran
    }
    return render(request, 'organizer/pembayaran.html', context)

@login_required
@require_POST # Hanya mengizinkan metode POST
def hapus_paket_view(request, paket_id):
    paket = get_object_or_404(Paket, id=paket_id)

    # Keamanan: Pastikan hanya pemilik yang bisa menghapus
    if paket.wo != request.user:
        messages.error(request, "Anda tidak memiliki izin untuk menghapus paket ini.")
        return redirect('kelola_paket')

    nama_paket_dihapus = paket.nama_paket
    paket.delete()
    messages.success(request, f"Paket '{nama_paket_dihapus}' telah berhasil dihapus.")
    
    return redirect('kelola_paket')

# --- PERBAIKAN: Menambahkan @login_required ---
@login_required
def tambah_gedung(request):
    # Cek apakah user adalah WO
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo':
        return redirect('index')

    if request.method == 'POST':
        # PENTING: request.FILES wajib ada untuk upload foto
        form = GedungForm(request.POST, request.FILES)
        
        if form.is_valid():
            gedung = form.save(commit=False)
            gedung.wo = request.user  # Set pemilik gedung ke user yg login
            gedung.save()
            
            messages.success(request, f"Gedung '{gedung.nama_gedung}' BERHASIL MASUK DATABASE!")
            return redirect('kelola_gedung')
        else:
            # Jika gagal, print error ke terminal (bawah VS Code)
            print("GAGAL MENYIMPAN GEDUNG:", form.errors)
            messages.error(request, "Gagal menyimpan. Cek terminal untuk detail error.")
    else:
        form = GedungForm()
    
    context = {
        'form': form,
        'page_title': 'Tambah Gedung Baru'
    }
    return render(request, 'organizer/tambah_gedung.html', context)

@login_required
def dashboard(request):
    """
    View untuk halaman dashboard utama WO.
    """
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo':
        return redirect('index')

    # Ambil data untuk dashboard
    jumlah_paket = Paket.objects.filter(wo=request.user).count()
    jumlah_gedung = Gedung.objects.filter(wo=request.user).count()
    pesanan_baru = Pesanan.objects.filter(paket__wo=request.user, status='menunggu').count()

    context = {
        'page_title': 'Dashboard WO',
        'jumlah_paket': jumlah_paket,
        'jumlah_gedung': jumlah_gedung,
        'pesanan_baru': pesanan_baru,
    }
    
    # Ambil juga data gedung untuk ditampilkan di dashboard SEMENTARA
    all_gedung = Gedung.objects.filter(wo=request.user).order_by('nama_gedung')
    context['all_gedung'] = all_gedung
    
    # Render template kelola_gedung.html sebagai dashboard SEMENTARA
    # Ini akan diperbaiki saat Anda membuat dashboard.html
    return render(request, 'organizer/kelola_gedung.html', context)

# --- INI FUNGSI YANG HILANG (PENYEBAB ERROR) ---
@login_required
def kelola_gedung(request):
    """
    View untuk menampilkan daftar semua gedung milik WO (desain kartu).
    """
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo':
        return redirect('index')

    # Ambil SEMUA gedung yang DIBUAT oleh WO yang sedang login
    all_gedung = Gedung.objects.filter(wo=request.user).order_by('nama_gedung')
    
    context = {
        'all_gedung': all_gedung,
        'page_title': 'Kelola Gedung Rekanan'
    }
    # Render template kelola_gedung.html
    return render(request, 'organizer/kelola_gedung.html', context)

@login_required
@require_POST # Hanya mengizinkan metode POST untuk keamanan
def hapus_gedung(request, gedung_id):
    """
    View untuk menghapus gedung berdasarkan ID.
    """
    # Ambil objek gedung, atau 404 jika tidak ada
    gedung = get_object_or_404(Gedung, id=gedung_id)

    # Keamanan: Pastikan hanya pemilik WO yang bisa menghapus
    if gedung.wo != request.user:
        messages.error(request, "Anda tidak memiliki izin untuk menghapus gedung ini.")
        return redirect('kelola_gedung')

    # Simpan nama untuk pesan sukses sebelum dihapus
    nama_gedung_dihapus = gedung.nama_gedung
    
    # Hapus objek dari database
    gedung.delete()
    
    messages.success(request, f"Gedung '{nama_gedung_dihapus}' telah berhasil dihapus.")
    
    # Kembali ke halaman kelola gedung
    return redirect('kelola_gedung')

@login_required
def edit_gedung(request, gedung_id):
    """
    View untuk mengedit gedung yang sudah ada.
    """
    # 1. Ambil data gedung berdasarkan ID, atau tampilkan 404 jika tidak ada
    gedung = get_object_or_404(Gedung, id=gedung_id)

    # 2. Keamanan: Cek apakah yang login adalah pemilik gedung ini?
    # Agar WO A tidak bisa mengedit gedung milik WO B
    if gedung.wo != request.user:
        messages.error(request, "Anda tidak memiliki izin untuk mengedit gedung ini.")
        return redirect('kelola_gedung')

    if request.method == 'POST':
        # 3. Jika tombol Simpan ditekan:
        # 'instance=gedung' memberitahu Django untuk MENG-UPDATE data ini, bukan membuat baru.
        form = GedungForm(request.POST, request.FILES, instance=gedung)
        if form.is_valid():
            form.save()
            messages.success(request, f"Gedung '{gedung.nama_gedung}' berhasil diperbarui.")
            return redirect('kelola_gedung')
    else:
        # 4. Jika baru membuka halaman (GET):
        # Isi formulir secara otomatis dengan data yang ada di database
        form = GedungForm(instance=gedung)
    
    context = {
        'form': form,
        # Judul halaman kita buat dinamis agar user tahu sedang mengedit
        'page_title': f'Edit Gedung: {gedung.nama_gedung}' 
    }
    
    # 5. PENTING: Kita GUNAKAN ULANG file 'tambah_gedung.html'
    # Kita tidak perlu membuat file HTML baru, karena strukturnya sama persis.
    return render(request, 'organizer/tambah_gedung.html', context)

