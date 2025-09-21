# organizer/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Pesanan, Paket
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import PaketForm, PesananForm
from .models import Pesanan, Paket, FotoPortofolio # <-- Tambahkan FotoPortofolio
from django.views.decorators.http import require_POST 





@login_required
def kelola_pesanan_view(request):
    # Pastikan hanya pengguna dengan peran WO yang bisa mengakses
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo':
        return redirect('index')

    # 1. Ambil pesanan yang masih aktif (masuk & dikonfirmasi)
    pesanan_masuk = Pesanan.objects.filter(
        paket__wo=request.user,
        status__in=['menunggu', 'dikonfirmasi']
    ).order_by('-tgl_pesan')

    # 2. Ambil pesanan yang sudah tidak aktif (riwayat)
    riwayat_pesanan = Pesanan.objects.filter(
        paket__wo=request.user,
        status__in=['selesai', 'dibatalkan']
    ).order_by('-tgl_pesan')

    context = {
        'pesanan_masuk': pesanan_masuk,
        'riwayat_pesanan': riwayat_pesanan,
    }
    return render(request, 'organizer/kelola_pesanan.html', context)

@login_required
def detail_pesanan_view(request, pesanan_id):
    pesanan = get_object_or_404(Pesanan, id=pesanan_id)

    # Keamanan: Pastikan WO yang login adalah pemilik pesanan ini
    if pesanan.paket.wo != request.user:
        messages.error(request, 'Anda tidak memiliki akses ke pesanan ini.')
        return redirect('kelola_pesanan')

    # Logika untuk menangani aksi konfirmasi atau tolak
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'confirm':
            pesanan.status = 'dikonfirmasi'
            messages.success(request, f"Pesanan #{pesanan.id} telah dikonfirmasi.")
        elif action == 'reject':
            pesanan.status = 'dibatalkan'
            # Ambil alasan dari form di pop-up
            alasan = request.POST.get('rejection_reason', '') 
            pesanan.catatan_pembatalan = alasan
            messages.warning(request, f"Pesanan #{pesanan.id} telah ditolak.")
        elif action == 'complete':
            pesanan.status = 'selesai'
            messages.info(request, f"Pesanan #{pesanan.id} telah ditandai selesai.")
        pesanan.save()
        return redirect('kelola_pesanan')

    context = {
        'pesanan': pesanan,
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

login_required
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

    context = {
        'form': form
    }
    return render(request, 'organizer/buat_paket.html', context)

@login_required
def buat_pesanan_view(request, paket_id):
    paket = get_object_or_404(Paket, id=paket_id)

    if not hasattr(request.user, 'profil') or request.user.profil.role != 'customer':
        messages.error(request, 'Hanya customer yang dapat membuat pesanan.')
        return redirect('detail_paket', paket_id=paket.id)

    if request.method == 'POST':
        form = PesananForm(request.POST)
        if form.is_valid():
            pesanan = form.save(commit=False)
            pesanan.paket = paket
            pesanan.customer = request.user
            pesanan.save()
            messages.success(request, f"Pesanan untuk '{paket.nama_paket}' telah berhasil dibuat. Mohon tunggu konfirmasi dari WO.")
            return redirect('pesanan_berhasil', pesanan_id=pesanan.id)
    else:
        form = PesananForm()

    context = {
        'form': form,
        'paket': paket
    }
    return render(request, 'organizer/buat_pesanan.html', context)

@login_required
def pesanan_berhasil_view(request, pesanan_id):
    pesanan = get_object_or_404(Pesanan, id=pesanan_id)

    # Keamanan: Pastikan hanya customer yang membuat pesanan yang bisa melihat halaman ini
    if pesanan.customer != request.user:
        return redirect('daftar_wo')

    context = {
        'pesanan': pesanan
    }
    return render(request, 'organizer/pesanan_berhasil.html', context)

@login_required
def edit_paket_view(request, paket_id):
    # Ambil paket yang akan diedit, atau tampilkan 404 jika tidak ada
    paket = get_object_or_404(Paket, id=paket_id)

    # Keamanan: Pastikan hanya pemilik yang bisa mengedit
    if paket.wo != request.user:
        messages.error(request, "Anda tidak memiliki izin untuk mengedit paket ini.")
        return redirect('kelola_paket')

    if request.method == 'POST':
        # 'instance=paket' memberitahu form untuk mengedit data yang ada
        form = PaketForm(request.POST, request.FILES, instance=paket)
        if form.is_valid():
            form.save()
            
            images = request.FILES.getlist('galeri_foto')
            for image in images:
                FotoPortofolio.objects.create(paket=paket, foto=image)
                
            messages.success(request, f"Paket '{paket.nama_paket}' berhasil diperbarui.")
            return redirect('kelola_paket')
    else:
        # 'instance=paket' akan mengisi form dengan data yang sudah ada
        form = PaketForm(instance=paket)

    context = {
        'form': form,
        'paket': paket
    }
    return render(request, 'organizer/edit_paket.html', context)

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


