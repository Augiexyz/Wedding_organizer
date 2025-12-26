from django.db import models
from django.conf import settings
from django.utils import timezone

# --- MODEL PAKET ---
class Paket(models.Model):
    # Pilihan Kategori untuk Paket (Logika Baru)
    KATEGORI_PAKET_CHOICES = [
        ('non_gedung', '❌ Tanpa Gedung / Venue Bebas'),
        ('S', '🏢 Gedung Small (S)'),
        ('M', '🏢 Gedung Medium (M)'),
        ('L', '🏢 Gedung Large (L)'),
    ]

    wo = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='paket_wo')
    nama_paket = models.CharField(max_length=100)
    harga = models.DecimalField(max_digits=12, decimal_places=2)
    deskripsi = models.TextField()
    foto = models.ImageField(upload_to='paket_fotos/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # PERUBAHAN UTAMA:
    # Paket sekarang menyimpan KATEGORI, bukan gedung spesifik
    kategori_gedung = models.CharField(
        max_length=20, 
        choices=KATEGORI_PAKET_CHOICES, 
        default='non_gedung',
        help_text="Tentukan apakah paket ini termasuk fasilitas gedung, dan kategori apa."
    )
    
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.nama_paket} ({self.get_kategori_gedung_display()})"

# --- MODEL GEDUNG ---
class Gedung(models.Model):
    KATEGORI_CHOICES = [
        ('S', 'S (Small)'),
        ('M', 'M (Medium)'),
        ('L', 'L (Large)'),
    ]

    wo = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='gedung_wo'
    )

    nama_gedung = models.CharField(max_length=100)
    lokasi = models.CharField(max_length=255) 
    kapasitas = models.CharField(max_length=100) 
    harga_sewa = models.DecimalField(max_digits=12, decimal_places=2)
    foto_gedung = models.ImageField(upload_to='gedung_photos/', null=True, blank=True)
    deskripsi = models.TextField(null=True, blank=True)
    
    # Kategori ini nanti akan dicocokkan dengan Paket
    kategori = models.CharField(max_length=1, choices=KATEGORI_CHOICES, default='M')
    fasilitas = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.nama_gedung} ({self.kategori})"

# --- MODEL PESANAN ---
class Pesanan(models.Model):
    STATUS_CHOICES = (
        ('menunggu', 'Menunggu Konfirmasi'),
        # PERBAIKAN: Hapus "(Belum Bayar)" agar tidak membingungkan
        ('dikonfirmasi', 'Dikonfirmasi'), 
        ('disiapkan', 'Sedang Disiapkan'), 
        ('selesai', 'Selesai'),
        ('dibatalkan', 'Dibatalkan'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('belum_bayar', 'Belum Dibayar'),
        ('lunas', 'Lunas'),
    )

    # ... (sisa field tetap sama) ...
    paket = models.ForeignKey(Paket, on_delete=models.CASCADE)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    gedung_dipilih = models.ForeignKey(Gedung, on_delete=models.SET_NULL, null=True, blank=True, related_name='pesanan_gedung')
    
    tgl_acara = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='menunggu')
    tgl_pesan = models.DateTimeField(auto_now_add=True)
    
    nama_pasangan = models.CharField(max_length=200, null=True)
    telepon = models.CharField(max_length=20, null=True)
    lokasi_acara = models.CharField(max_length=255, null=True, help_text="Diisi manual jika paket Tanpa Gedung")
    jumlah_tamu = models.IntegerField(null=True)
    catatan = models.TextField(blank=True, null=True)
    
    status_pembayaran = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='belum_bayar')
    catatan_pembatalan = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Pesanan {self.paket.nama_paket} oleh {self.customer.username}"
    
# --- MODEL GALERI ---
class FotoPortofolio(models.Model):
    paket = models.ForeignKey(Paket, related_name='galeri', on_delete=models.CASCADE)
    foto = models.ImageField(upload_to='galeri_paket/')
    
class FotoGedung(models.Model):
    gedung = models.ForeignKey(Gedung, on_delete=models.CASCADE, related_name='galeri_gedung')
    foto = models.ImageField(upload_to='gedung_galeri/')

    def __str__(self):
        return f"Foto untuk {self.gedung.nama_gedung}"
    
class Ulasan(models.Model):
    wo = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ulasan_wo')
    penulis = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='penulis_ulasan')
    
    # --- FIELD BARU: KUNCI AGAR 1 PESANAN = 1 ULASAN ---
    pesanan = models.OneToOneField(Pesanan, on_delete=models.CASCADE, null=True, blank=True, related_name='data_ulasan')
    # ---------------------------------------------------
    
    rating = models.IntegerField(default=5, choices=[(i, i) for i in range(1, 6)])
    komentar = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ulasan oleh {self.penulis.username} untuk {self.wo.profilwo.nama_brand}"