# pengguna/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .models import Profil, ProfilWO, GaleriWO # <-- UBAH BARIS INI UNTUK MENYERTAKAN PROFILWO
from .forms import RegistrasiForm, ProfilWOForm
from django.db.models import Sum, Count # Import Sum dan Count
from organizer.models import Pesanan, Paket    # Import model Pesanan
from django.db.models.functions import TruncMonth # <-- Import TruncMonth
import json 
from .forms import UserUpdateForm, CustomPasswordChangeForm


# ... (Fungsi registrasi_view Anda) ...
def registrasi_view(request):
    if request.method == 'POST':
        form = RegistrasiForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            nama_lengkap = form.cleaned_data.get('nama_lengkap')
            nama_split = nama_lengkap.split(' ', 1)
            user.first_name = nama_split[0]
            if len(nama_split) > 1:
                user.last_name = nama_split[1]
            
            user.save() 

            Profil.objects.create(
                user=user,
                role=form.cleaned_data.get('role')
            )

            login(request, user)
            messages.success(request, f'Selamat datang, {user.username}! Akun Anda berhasil dibuat.')
            return redirect('redirect_after_login')
    else:
        form = RegistrasiForm()
    return render(request, 'pengguna/registrasi.html', {'form': form})


@login_required
def buat_profil_wo_view(request):
    if request.user.profil.role != 'wo':
        return redirect('index')

    if request.method == 'POST':
        form = ProfilWOForm(request.POST, request.FILES)
        if form.is_valid():
            profil_wo = form.save(commit=False)
            profil_wo.user = request.user
            profil_wo.save()
            messages.success(request, 'Profil WO Anda berhasil dibuat!')
            return redirect('dashboard_wo')
    else:
        form = ProfilWOForm()

    return render(request, 'pengguna/buat_profil_wo.html', {'form': form})


@login_required
def redirect_after_login_view(request):
    user = request.user

    # 1. Cek apakah User memiliki Profil
    # Menggunakan hasattr untuk mengecek keberadaan relasi 'profil'
    if hasattr(user, 'profil'):
        role = user.profil.role
        if role == 'wo':
            return redirect('dashboard_wo')
        elif role == 'customer':
            # Cek parameter 'next' jika ada (misal redirect setelah login paksa)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('index')
    
    # 2. Jika TIDAK punya profil, cek apakah dia Superuser/Admin
    elif user.is_superuser:
        # Arahkan admin langsung ke panel admin Django
        return redirect('/admin/')
    
    # 3. Jika user biasa tapi data profil rusak/hilang
    else:
        messages.error(request, "Akun Anda tidak memiliki profil yang valid. Silakan hubungi admin.")
        return redirect('index')

@login_required
def dashboard_wo_view(request):
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo':
        return redirect('index')
    
    try:
        profil_wo = request.user.profilwo
    except ProfilWO.DoesNotExist:
        return redirect('buat_profil_wo')

    # --- LOGIKA BARU DIMULAI DI SINI ---

    # Mengambil semua pesanan yang ditujukan untuk WO yang sedang login
    semua_pesanan = Pesanan.objects.filter(paket__wo=request.user)

    # Menghitung statistik
    pesanan_baru_count = semua_pesanan.filter(status='menunggu').count()
    pesanan_selesai_count = semua_pesanan.filter(status='selesai').count()
    
    # Menghitung pendapatan dari pesanan yang selesai
    pendapatan_data = semua_pesanan.filter(status='selesai').aggregate(total=Sum('paket__harga'))
    pendapatan_total = pendapatan_data['total'] or 0

    # Mengambil 5 pesanan terbaru
    pesanan_terbaru = semua_pesanan.order_by('-tgl_pesan')[:5]
    
    paket_populer = Paket.objects.filter(wo=request.user, is_active=True) \
        .annotate(jumlah_pesanan=Count('pesanan')) \
        .order_by('-jumlah_pesanan')[:4]
        
    # --- LOGIKA BARU UNTUK GRAFIK ---
    # Mengelompokkan pendapatan per bulan dari pesanan yang selesai
    data_grafik = Pesanan.objects.filter(
        paket__wo=request.user,
        status='selesai'
    ).annotate(
        bulan=TruncMonth('tgl_acara')
    ).values('bulan').annotate(
        total_pendapatan=Sum('paket__harga')
    ).order_by('bulan')

    # Memformat data agar bisa dibaca oleh Chart.js
    chart_labels = [data['bulan'].strftime('%b') for data in data_grafik]
    chart_data = [int(data['total_pendapatan'] / 1000000) for data in data_grafik] # Dalam jutaan


    context = {
        'profil_wo': profil_wo,
        'pesanan_baru_count': pesanan_baru_count,
        'pesanan_selesai_count': pesanan_selesai_count,
        'pendapatan_total': pendapatan_total,
        'pesanan_terbaru': pesanan_terbaru,
        'paket_populer': paket_populer,
        'chart_labels': json.dumps(chart_labels), # <-- Gunakan json.dumps untuk keamanan
        'chart_data': json.dumps(chart_data),
        

    }
    return render(request, 'pengguna/dashboard_wo.html', context)

@login_required
def edit_profil_wo_view(request):
    # Pastikan hanya WO yang bisa mengakses dan sudah punya profil
    try:
        profil_wo = request.user.profilwo
    except ProfilWO.DoesNotExist:
        # Jika profil belum ada, paksa buat dulu
        return redirect('buat_profil_wo')

    if request.method == 'POST':
        # 'instance=profil_wo' memberitahu form untuk mengedit data yang ada
        form = ProfilWOForm(request.POST, request.FILES, instance=profil_wo)
        if form.is_valid():
            form.save()
            
            images = request.FILES.getlist('galeri_wo_foto')
            for image in images:
                GaleriWO.objects.create(profil_wo=profil_wo, foto=image)
                
            messages.success(request, 'Profil Anda berhasil diperbarui.')
            return redirect('edit_profil_wo') # Kembali ke halaman ini setelah menyimpan
    else:
        # 'instance=profil_wo' akan mengisi form dengan data yang ada
        form = ProfilWOForm(instance=profil_wo)

    context = {
        'form': form,
        'profil_wo': profil_wo # Kirim profil untuk menampilkan logo
    }
    return render(request, 'pengguna/edit_profil_wo.html', context)

@login_required
def edit_profil_customer_view(request):
    if request.method == 'POST':
        # Cek form mana yang disubmit
        if 'update_profile' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            password_form = CustomPasswordChangeForm(request.user)
            if user_form.is_valid():
                # Pisahkan nama lengkap menjadi nama depan dan belakang
                nama_lengkap = user_form.cleaned_data.get('nama_lengkap')
                nama_split = nama_lengkap.split(' ', 1)
                request.user.first_name = nama_split[0]
                if len(nama_split) > 1:
                    request.user.last_name = nama_split[1]
                request.user.save()
                messages.success(request, 'Informasi profil Anda berhasil diperbarui.')
                return redirect('edit_profil_customer')
        
        elif 'change_password' in request.POST:
            password_form = CustomPasswordChangeForm(request.user, request.POST)
            user_form = UserUpdateForm(instance=request.user, initial={'nama_lengkap': request.user.get_full_name()})
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Penting agar user tidak logout
                messages.success(request, 'Password Anda berhasil diubah.')
                return redirect('edit_profil_customer')
    else:
        user_form = UserUpdateForm(instance=request.user, initial={'nama_lengkap': request.user.get_full_name()})
        password_form = CustomPasswordChangeForm(request.user)

    context = {
        'user_form': user_form,
        'password_form': password_form,
    }
    return render(request, 'pengguna/edit_profil_customer.html', context)