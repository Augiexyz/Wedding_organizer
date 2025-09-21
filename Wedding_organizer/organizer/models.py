# organizer/models.py

from django.db import models
from django.contrib.auth.models import User

class Paket(models.Model):
    wo = models.ForeignKey(User, on_delete=models.CASCADE) # WO yang memiliki paket ini
    nama_paket = models.CharField(max_length=100)
    harga = models.DecimalField(max_digits=10, decimal_places=2)
    deskripsi = models.TextField()
    foto = models.ImageField(upload_to='paket_fotos/', null=True, blank=True) # <-- TAMBAHKAN INI
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nama_paket} - {self.wo.profilwo.nama_brand}"

class Pesanan(models.Model):
    STATUS_CHOICES = (
        ('menunggu', 'Menunggu Konfirmasi'),
        ('dikonfirmasi', 'Dikonfirmasi'),
        ('selesai', 'Selesai'),
        ('dibatalkan', 'Dibatalkan'),
    )

    paket = models.ForeignKey(Paket, on_delete=models.CASCADE)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    tgl_acara = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='menunggu')
    tgl_pesan = models.DateTimeField(auto_now_add=True)
    
    nama_pasangan = models.CharField(max_length=200, null=True)
    telepon = models.CharField(max_length=20, null=True)
    lokasi_acara = models.CharField(max_length=255, null=True)
    jumlah_tamu = models.IntegerField(null=True)
    catatan = models.TextField(blank=True, null=True)
    catatan_pembatalan = models.TextField(blank=True, null=True, help_text="Alasan jika pesanan ditolak oleh WO")

    def __str__(self):
        return f"Pesanan {self.paket.nama_paket} oleh {self.customer.username}"
    
    PAYMENT_STATUS_CHOICES = (
        ('belum_bayar', 'Belum Dibayar'),
        ('lunas', 'Lunas'),
    )
    status_pembayaran = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='belum_bayar'
    )
    catatan_pembatalan = models.TextField(blank=True, null=True, help_text="Alasan jika pesanan ditolak oleh WO")

    def __str__(self):
        return f"Pesanan {self.paket.nama_paket} oleh {self.customer.username}"
    
class FotoPortofolio(models.Model):
    paket = models.ForeignKey(Paket, related_name='galeri', on_delete=models.CASCADE)
    foto = models.ImageField(upload_to='galeri_paket/')

    def __str__(self):
        return f"Foto untuk {self.paket.nama_paket}"