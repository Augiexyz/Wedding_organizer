from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .models import Profil, ProfilWO, GaleriWO 
from .forms import RegistrasiForm, ProfilWOForm, UserUpdateForm, CustomPasswordChangeForm
# Tambahkan Avg untuk hitung rata-rata rating
from django.db.models import Sum, Count, Avg 
# Tambahkan model Ulasan
from organizer.models import Pesanan, Paket, Ulasan 
from django.db.models.functions import TruncMonth
import json 

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

    if hasattr(user, 'profil'):
        role = user.profil.role
        if role == 'wo':
            return redirect('dashboard_wo')
        elif role == 'customer':
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('index')
    
    elif user.is_superuser:
        return redirect('/admin/')
    
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

    # Mengambil semua pesanan yang ditujukan untuk WO yang sedang login
    # Optimasi: Gunakan select_related untuk mempercepat query paket & customer
    semua_pesanan = Pesanan.objects.filter(paket__wo=request.user).select_related('paket', 'customer')

    # Menghitung statistik
    pesanan_baru_count = semua_pesanan.filter(status='menunggu').count()
    pesanan_selesai_count = semua_pesanan.filter(status='selesai').count()
    
    # Menghitung pendapatan dari pesanan yang selesai
    pendapatan_data = semua_pesanan.filter(status='selesai').aggregate(total=Sum('paket__harga'))
    pendapatan_total = pendapatan_data['total'] or 0

    # Mengambil 5 pesanan terbaru
    pesanan_terbaru = semua_pesanan.order_by('-tgl_pesan')[:5]
    
    # Paket Populer
    paket_populer = Paket.objects.filter(wo=request.user, is_active=True) \
        .annotate(jumlah_pesanan=Count('pesanan')) \
        .order_by('-jumlah_pesanan')[:4]
        
    # --- LOGIKA BARU UNTUK GRAFIK: PERFORMA PAKET ---
    # Mengelompokkan pendapatan berdasarkan Nama Paket
    data_grafik = Pesanan.objects.filter(
        paket__wo=request.user,
        status='selesai'
    ).values('paket__nama_paket').annotate(
        total_pendapatan=Sum('paket__harga')
    ).order_by('-total_pendapatan')

    # Label grafik sekarang adalah Nama Paket
    chart_labels = [data['paket__nama_paket'] for data in data_grafik]
    # Data grafik adalah total pendapatan paket tersebut (dalam jutaan)
    chart_data = [int(data['total_pendapatan'] / 1000000) for data in data_grafik]

    # --- BAGIAN BARU: DATA ULASAN ---
    ulasan_list = Ulasan.objects.filter(wo=request.user).order_by('-created_at')
    rating_rata2 = ulasan_list.aggregate(Avg('rating'))['rating__avg'] or 0
    # --------------------------------

    context = {
        'profil_wo': profil_wo,
        'pesanan_baru_count': pesanan_baru_count,
        'pesanan_selesai_count': pesanan_selesai_count,
        'pendapatan_total': pendapatan_total,
        'pesanan_terbaru': pesanan_terbaru,
        'paket_populer': paket_populer,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        
        # Kirim data ulasan ke template
        'ulasan_list': ulasan_list,
        'rating_rata2': round(rating_rata2, 1),
    }
    return render(request, 'pengguna/dashboard_wo.html', context)

@login_required
def edit_profil_wo_view(request):
    try:
        profil_wo = request.user.profilwo
    except ProfilWO.DoesNotExist:
        return redirect('buat_profil_wo')

    if request.method == 'POST':
        form = ProfilWOForm(request.POST, request.FILES, instance=profil_wo)
        if form.is_valid():
            form.save()
            
            images = request.FILES.getlist('galeri_wo_foto')
            for image in images:
                GaleriWO.objects.create(profil_wo=profil_wo, foto=image)
                
            messages.success(request, 'Profil Anda berhasil diperbarui.')
            return redirect('edit_profil_wo')
    else:
        form = ProfilWOForm(instance=profil_wo)

    context = {
        'form': form,
        'profil_wo': profil_wo
    }
    return render(request, 'pengguna/edit_profil_wo.html', context)

@login_required
def edit_profil_customer_view(request):
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            password_form = CustomPasswordChangeForm(request.user)
            if user_form.is_valid():
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
                update_session_auth_hash(request, user)
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