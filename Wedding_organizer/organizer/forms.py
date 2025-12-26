from django import forms
from .models import Gedung, Paket, Pesanan, Ulasan

class PaketForm(forms.ModelForm):
    class Meta:
        model = Paket
        # PERUBAHAN PENTING:
        # Kita ganti 'gedung' menjadi 'kategori_gedung' sesuai models.py baru
        fields = ['nama_paket', 'harga', 'deskripsi', 'foto', 'is_active', 'kategori_gedung']

    def __init__(self, *args, **kwargs):
        super(PaketForm, self).__init__(*args, **kwargs)

        input_field_class = 'input-field'

        # Styling untuk input standar
        self.fields['nama_paket'].widget.attrs.update({
            'class': input_field_class, 'placeholder': 'Contoh: Paket Diamond'
        })
        self.fields['harga'].widget.attrs.update({
            'class': input_field_class, 'placeholder': 'Contoh: 50000000'
        })
        self.fields['deskripsi'].widget.attrs.update({
            'class': f'{input_field_class} h-40',
            'placeholder': 'Tulis setiap layanan dalam baris baru. Contoh:\n- Tim Hari-H (6 orang)\n- Rekomendasi Vendor'
        })
        self.fields['foto'].widget.attrs.update({
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-pink-50 file:text-pink-700 hover:file:bg-pink-100'
        })
        self.fields['is_active'].widget.attrs.update({
            'class': 'h-5 w-5 rounded text-pink-600 focus:ring-pink-500'
        })

        # --- LOGIKA BARU UNTUK KATEGORI GEDUNG ---
        # Field ini sekarang adalah dropdown pilihan statis (S/M/L/Non)
        self.fields['kategori_gedung'].widget.attrs.update({'class': input_field_class})
        self.fields['kategori_gedung'].label = "Termasuk Fasilitas Gedung?"
        # -----------------------------------------

class PesananForm(forms.ModelForm):
    class Meta:
        model = Pesanan
        fields = [
            'nama_pasangan', 'telepon', 'tgl_acara', 
            'lokasi_acara', 'jumlah_tamu', 'catatan', 'gedung_dipilih'
        ]
        widgets = {
            'tgl_acara': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        paket = kwargs.pop('paket', None) 
        super(PesananForm, self).__init__(*args, **kwargs)
        
        input_css = 'input-field'
        self.fields['nama_pasangan'].widget.attrs.update({'class': input_css, 'placeholder': 'Contoh: Budi & Wati'})
        self.fields['telepon'].widget.attrs.update({'class': input_css, 'placeholder': 'Nomor WA aktif'})
        self.fields['tgl_acara'].widget.attrs.update({'class': input_css})
        self.fields['lokasi_acara'].widget.attrs.update({'class': input_css, 'placeholder': 'Alamat lokasi acara (jika di rumah/gedung sendiri)'})
        self.fields['jumlah_tamu'].widget.attrs.update({'class': input_css, 'placeholder': 'Contoh: 500'})
        self.fields['catatan'].widget.attrs.update({'class': f'{input_css} h-24', 'placeholder': 'Permintaan khusus...'})
        
        # Logika Filter Gedung
        self.fields['gedung_dipilih'].widget.attrs.update({'class': input_css})
        self.fields['gedung_dipilih'].label = "Pilih Gedung (Sesuai Paket)"
        self.fields['gedung_dipilih'].empty_label = "Pilih Gedung..."

        if paket:
            if paket.kategori_gedung == 'non_gedung':
                self.fields['gedung_dipilih'].widget = forms.HiddenInput()
                self.fields['gedung_dipilih'].required = False
                self.fields['gedung_dipilih'].queryset = Gedung.objects.none()
            else:
                self.fields['gedung_dipilih'].queryset = Gedung.objects.filter(
                    wo=paket.wo, 
                    kategori=paket.kategori_gedung
                )
                self.fields['gedung_dipilih'].required = True
                self.fields['lokasi_acara'].required = False
                self.fields['lokasi_acara'].widget.attrs.update({
                    'placeholder': 'Lokasi otomatis sesuai gedung yang dipilih',
                    'disabled': 'disabled',
                    'class': 'input-field bg-gray-100 text-gray-500 cursor-not-allowed'
                })
                self.fields['lokasi_acara'].label = "Lokasi Acara (Otomatis)"

class GedungForm(forms.ModelForm):
    class Meta:
        model = Gedung
        fields = [
            'nama_gedung', 'lokasi', 'kapasitas', 'kategori',
            'harga_sewa', 'deskripsi', 'fasilitas', 'foto_gedung'
        ]

        widgets = {
            'nama_gedung': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Contoh: The Grand Ballroom'}),
            'lokasi': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Contoh: Jakarta Selatan'}),
            'kapasitas': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Contoh: 500 - 1000 Tamu'}),
            'kategori': forms.Select(attrs={'class': 'input-field'}),
            'harga_sewa': forms.NumberInput(attrs={'class': 'input-field', 'placeholder': 'Contoh: 150000000'}),
            'deskripsi': forms.Textarea(attrs={'class': 'input-field', 'rows': 4, 'placeholder': 'Jelaskan keunggulan dan suasana dari gedung ini.'}),
            'fasilitas': forms.Textarea(attrs={'class': 'input-field', 'rows': 4, 'placeholder': 'Tulis setiap fasilitas dalam baris baru. Contoh:\n- Full AC\n- Area Parkir Luas'}),
            'foto_gedung': forms.ClearableFileInput(attrs={'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-pink-50 file:text-pink-700 hover:file:bg-pink-100'}),
        }

        labels = {
            'nama_gedung': 'Nama Gedung',
            'harga_sewa': 'Harga Sewa (Rp)',
            'foto_gedung': 'Foto Utama Gedung',
            'kategori': 'Kategori Gedung',
            'fasilitas': 'Fasilitas Utama',
            'deskripsi': 'Deskripsi Gedung'
        }
        
class UlasanForm(forms.ModelForm):
    class Meta:
        model = Ulasan
        fields = ['rating', 'komentar']
        widgets = {
            'rating': forms.Select(attrs={'class': 'input-field w-full md:w-auto'}), # Dropdown angka 1-5
            'komentar': forms.Textarea(attrs={
                'class': 'input-field', 
                'rows': 3, 
                'placeholder': 'Bagikan pengalaman Anda menggunakan jasa WO ini...'
            }),
        }
        labels = {
            'rating': 'Berikan Rating (Bintang)',
            'komentar': 'Ulasan Anda'
        }