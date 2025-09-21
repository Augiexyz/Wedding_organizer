# organizer/forms.py

from django import forms
from .models import Paket, Pesanan

class PaketForm(forms.ModelForm):
    class Meta:
        model = Paket
        # PASTIKAN 'foto' ADA DI DALAM DAFTAR INI
        fields = ['nama_paket', 'harga', 'deskripsi', 'foto', 'is_active']

    def __init__(self, *args, **kwargs):
        super(PaketForm, self).__init__(*args, **kwargs)
        
        # Definisikan kelas CSS
        input_field_class = 'input-field'
        
        # Terapkan kelas ke setiap field
        self.fields['nama_paket'].widget.attrs.update({
            'class': input_field_class, 'placeholder': 'Contoh: Paket Diamond'
        })
        self.fields['harga'].widget.attrs.update({
            'class': input_field_class, 'placeholder': 'Contoh: 50000000'
        })
        self.fields['deskripsi'].widget.attrs.update({
            'class': f'{input_field_class} h-40', # Perbesar textarea
            'placeholder': 'Tulis setiap layanan dalam baris baru. Contoh:\n- Tim Hari-H (6 orang)\n- Rekomendasi Vendor'
        })
        self.fields['foto'].widget.attrs.update({
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-pink-50 file:text-pink-700 hover:file:bg-pink-100'
        })
        self.fields['is_active'].widget.attrs.update({
            'class': 'h-5 w-5 rounded text-pink-600 focus:ring-pink-500'
        })
        
        
class PesananForm(forms.ModelForm):
    class Meta:
        model = Pesanan
        fields = [
            'nama_pasangan', 'telepon', 'tgl_acara', 
            'lokasi_acara', 'jumlah_tamu', 'catatan'
        ]
        widgets = {
            'tgl_acara': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super(PesananForm, self).__init__(*args, **kwargs)
        
        # Styling untuk PesananForm
        self.fields['nama_pasangan'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Contoh: Budi & Wati'})
        self.fields['telepon'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Nomor yang bisa dihubungi'})
        self.fields['tgl_acara'].widget.attrs.update({'class': 'input-field'})
        self.fields['lokasi_acara'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Contoh: Gedung Serbaguna, Samarinda'})
        self.fields['jumlah_tamu'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Contoh: 500'})
        self.fields['catatan'].widget.attrs.update({'class': 'input-field h-24', 'placeholder': 'Apakah ada permintaan khusus...'})