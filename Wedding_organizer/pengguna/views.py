from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .models import Profil, ProfilWO, GaleriWO 
from .forms import RegistrasiForm, ProfilWOForm, UserUpdateForm, CustomPasswordChangeForm
from django.db.models import Sum, Count, Avg 
from organizer.models import Pesanan, Paket, Ulasan 
from django.db.models.functions import TruncMonth
import json 

# --- IMPORT KHUSUS FITUR LUPA PASSWORD ---
import random
from django import forms
from django.contrib.auth.models import User
# -----------------------------------------

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
            Profil.objects.create(user=user, role=form.cleaned_data.get('role'))
            login(request, user)
            messages.success(request, f'Selamat datang, {user.username}! Akun Anda berhasil dibuat.')
            return redirect('redirect_after_login')
    else:
        form = RegistrasiForm()
    return render(request, 'pengguna/registrasi.html', {'form': form})

@login_required
def buat_profil_wo_view(request):
    if request.user.profil.role != 'wo': return redirect('index')
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
        if role == 'wo': return redirect('dashboard_wo')
        elif role == 'customer':
            next_url = request.GET.get('next')
            if next_url: return redirect(next_url)
            return redirect('index')
    elif user.is_superuser: return redirect('/admin/')
    else:
        messages.error(request, "Akun Anda tidak memiliki profil yang valid.")
        return redirect('index')

@login_required
def dashboard_wo_view(request):
    if not hasattr(request.user, 'profil') or request.user.profil.role != 'wo': return redirect('index')
    try: profil_wo = request.user.profilwo
    except ProfilWO.DoesNotExist: return redirect('buat_profil_wo')

    semua_pesanan = Pesanan.objects.filter(paket__wo=request.user).select_related('paket', 'customer')
    pesanan_baru_count = semua_pesanan.filter(status='menunggu').count()
    pesanan_selesai_count = semua_pesanan.filter(status='selesai').count()
    pendapatan_data = semua_pesanan.filter(status='selesai').aggregate(total=Sum('paket__harga'))
    pendapatan_total = pendapatan_data['total'] or 0
    pesanan_terbaru = semua_pesanan.order_by('-tgl_pesan')[:5]
    paket_populer = Paket.objects.filter(wo=request.user, is_active=True).annotate(jumlah_pesanan=Count('pesanan')).order_by('-jumlah_pesanan')[:4]
    
    data_grafik = Pesanan.objects.filter(paket__wo=request.user, status='selesai').values('paket__nama_paket').annotate(total_pendapatan=Sum('paket__harga')).order_by('-total_pendapatan')
    chart_labels = [data['paket__nama_paket'] for data in data_grafik]
    chart_data = [int(data['total_pendapatan'] / 1000000) for data in data_grafik]
    ulasan_list = Ulasan.objects.filter(wo=request.user).order_by('-created_at')
    rating_rata2 = ulasan_list.aggregate(Avg('rating'))['rating__avg'] or 0

    context = {
        'profil_wo': profil_wo, 'pesanan_baru_count': pesanan_baru_count, 'pesanan_selesai_count': pesanan_selesai_count,
        'pendapatan_total': pendapatan_total, 'pesanan_terbaru': pesanan_terbaru, 'paket_populer': paket_populer,
        'chart_labels': json.dumps(chart_labels), 'chart_data': json.dumps(chart_data),
        'ulasan_list': ulasan_list, 'rating_rata2': round(rating_rata2, 1),
    }
    return render(request, 'pengguna/dashboard_wo.html', context)

@login_required
def edit_profil_wo_view(request):
    try: profil_wo = request.user.profilwo
    except ProfilWO.DoesNotExist: return redirect('buat_profil_wo')
    if request.method == 'POST':
        form = ProfilWOForm(request.POST, request.FILES, instance=profil_wo)
        if form.is_valid():
            form.save()
            images = request.FILES.getlist('galeri_wo_foto')
            for image in images: GaleriWO.objects.create(profil_wo=profil_wo, foto=image)
            messages.success(request, 'Profil Anda berhasil diperbarui.')
            return redirect('edit_profil_wo')
    else: form = ProfilWOForm(instance=profil_wo)
    return render(request, 'pengguna/edit_profil_wo.html', {'form': form, 'profil_wo': profil_wo})

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
                if len(nama_split) > 1: request.user.last_name = nama_split[1]
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
    return render(request, 'pengguna/edit_profil_customer.html', {'user_form': user_form, 'password_form': password_form})


# =========================================================
#  FITUR SIMULASI LUPA PASSWORD (OTP) - UPDATED (USERNAME)
# =========================================================

# 1. Form Meminta Username (Bukan Email)
class LupaPasswordForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'input-field', 
        'placeholder': 'Masukkan username Anda'
    }))

class OTPForm(forms.Form):
    otp = forms.CharField(max_length=4, widget=forms.TextInput(attrs={
        'class': 'input-field text-center text-2xl tracking-widest font-mono', 
        'placeholder': '0000',
        'maxlength': '4'
    }))

class ResetPasswordForm(forms.Form):
    password_baru = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input-field', 'placeholder': 'Password baru'}))
    konfirmasi_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input-field', 'placeholder': 'Ulangi password baru'}))

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password_baru")
        p2 = cleaned_data.get("konfirmasi_password")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Password tidak sama. Silakan ulangi.")

# 2. View Lupa Password (Cek Username -> Ambil Email -> Kirim OTP)
def lupa_password_view(request):
    if request.method == 'POST':
        form = LupaPasswordForm(request.POST)
        if form.is_valid():
            username_input = form.cleaned_data['username']
            
            # Cari user berdasarkan Username
            try:
                user = User.objects.get(username=username_input)
                email_user = user.email
                
                # Simulasi kirim OTP (walau input username, OTP 'ceritanya' dikirim ke email/hp user tsb)
                otp_code = str(random.randint(1000, 9999))
                
                # Simpan data reset ke session
                request.session['reset_otp'] = otp_code
                request.session['reset_username'] = username_input # Simpan username untuk tahap akhir
                
                # Kirim Notifikasi Simulasi
                if email_user:
                    pesan_simulasi = f"🔔 [SIMULASI SMS ke email {email_user}] Kode OTP: {otp_code}. Jangan berikan kepada siapapun."
                else:
                    pesan_simulasi = f"🔔 [SIMULASI SMS] Kode OTP: {otp_code} (User ini tidak punya email, tapi OTP tetap digenerate)."
                
                messages.info(request, pesan_simulasi)
                return redirect('verifikasi_otp')
                
            except User.DoesNotExist:
                messages.error(request, "Username tidak ditemukan.")
    else:
        form = LupaPasswordForm()
    
    return render(request, 'pengguna/lupa_password.html', {'form': form})

def verifikasi_otp_view(request):
    if 'reset_otp' not in request.session:
        return redirect('lupa_password')
    
    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            input_otp = form.cleaned_data['otp']
            session_otp = request.session.get('reset_otp')
            
            if input_otp == session_otp:
                request.session['otp_verified'] = True
                messages.success(request, "OTP Valid! Silakan buat password baru.")
                return redirect('reset_password')
            else:
                messages.error(request, "Kode OTP salah! Cek notifikasi sistem Anda.")
    else:
        form = OTPForm()
    
    return render(request, 'pengguna/verifikasi_otp.html', {'form': form})

# 3. Reset Password (Pakai session username)
def reset_password_view(request):
    if not request.session.get('otp_verified'):
        return redirect('lupa_password')
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            username = request.session.get('reset_username')
            password_baru = form.cleaned_data['password_baru']
            
            try:
                user = User.objects.get(username=username)
                user.set_password(password_baru)
                user.save()
                
                # Bersihkan session
                request.session.pop('reset_otp', None)
                request.session.pop('reset_username', None)
                request.session.pop('otp_verified', None)
                
                messages.success(request, "Password berhasil diubah! Silakan login.")
                return redirect('login') 
            except User.DoesNotExist:
                messages.error(request, "Terjadi kesalahan sistem.")
    else:
        form = ResetPasswordForm()
    
    return render(request, 'pengguna/reset_password.html', {'form': form})