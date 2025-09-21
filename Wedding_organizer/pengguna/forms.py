# pengguna/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profil, ProfilWO
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm



class RegistrasiForm(UserCreationForm):
    nama_lengkap = forms.CharField(max_length=100, required=True, label='Nama Lengkap')
    email = forms.EmailField(required=True)
    
    role = forms.ChoiceField(
        choices=Profil.ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'w-4 h-4 text-pink-500 border-pink-300 focus:ring-pink-500'}),
        initial='customer'
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'nama_lengkap')

    def __init__(self, *args, **kwargs):
        super(RegistrasiForm, self).__init__(*args, **kwargs)
        
        common_class = 'input-focus w-full px-3 py-2.5 border border-pink-200 rounded-lg bg-white/50 text-gray-800 placeholder-gray-500 transition-all duration-200'
        
        self.fields['username'].widget.attrs.update({'class': common_class, 'placeholder': 'Pilih username unik'})
        self.fields['nama_lengkap'].widget.attrs.update({'class': common_class, 'placeholder': 'Masukkan nama lengkap Anda'})
        self.fields['email'].widget.attrs.update({'class': common_class, 'placeholder': 'nama@email.com'})
        self.fields['password1'].widget.attrs.update({'class': common_class, 'placeholder': 'Minimal 8 karakter'})
        self.fields['password2'].widget.attrs.update({'class': common_class, 'placeholder': 'Ulangi password Anda'})


class ProfilWOForm(forms.ModelForm):
    class Meta:
        model = ProfilWO
        exclude = ['user']
        fields = ['nama_brand', 'logo', 'foto_sampul', 'deskripsi', 'telepon', 'email_bisnis', 'alamat']


    def __init__(self, *args, **kwargs):
        super(ProfilWOForm, self).__init__(*args, **kwargs)
        
        input_class = 'input-field'
        
        self.fields['nama_brand'].widget.attrs.update({'class': input_class, 'placeholder': 'Contoh: Wedding Impian Kita'})
        self.fields['deskripsi'].widget.attrs.update({'class': input_class, 'placeholder': 'Jelaskan tentang layanan WO Anda...'})
        self.fields['telepon'].widget.attrs.update({'class': input_class, 'placeholder': '0812xxxxxxxx'})
        self.fields['email_bisnis'].widget.attrs.update({'class': input_class, 'placeholder': 'kontak@weddingimpian.com'})
        self.fields['alamat'].widget.attrs.update({'class': input_class, 'placeholder': 'Jalan, Kota, Provinsi, Kode Pos'})
        self.fields['logo'].widget.attrs.update({'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-pink-50 file:text-pink-700 hover:file:bg-pink-100'})
        self.fields['foto_sampul'].widget.attrs.update({'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-pink-50 file:text-pink-700 hover:file:bg-pink-100'})
class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

        common_class = 'mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-400 focus:border-transparent'

        self.fields['username'].widget.attrs.update({
            'class': common_class,
            'placeholder': 'Username Anda'
        })
        self.fields['password'].widget.attrs.update({
            'class': common_class,
            'placeholder': 'Password'
        })
        
class UserUpdateForm(forms.ModelForm):
    nama_lengkap = forms.CharField(max_length=100, required=True, label="Nama Lengkap")

    class Meta:
        model = User
        fields = ['nama_lengkap', 'email']

    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.fields['email'].disabled = True # Membuat field email tidak bisa diedit
        self.fields['email'].widget.attrs.update({'class': 'input-field bg-gray-100'})
        self.fields['nama_lengkap'].widget.attrs.update({'class': 'input-field'})


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(CustomPasswordChangeForm, self).__init__(*args, **kwargs)
        
        input_class = 'input-field'
        
        self.fields['old_password'].widget.attrs.update({'class': input_class, 'placeholder': 'Masukkan password Anda saat ini'})
        self.fields['new_password1'].widget.attrs.update({'class': input_class, 'placeholder': 'Masukkan password baru'})
        self.fields['new_password2'].widget.attrs.update({'class': input_class, 'placeholder': 'Ulangi password baru'})