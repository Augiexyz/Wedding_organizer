# pengguna/models.py

from django.db import models
from django.contrib.auth.models import User

class Profil(models.Model):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('wo', 'Penyedia WO'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')

    def __str__(self):
        return f'{self.user.username} - {self.get_role_display()}'
    

class ProfilWO(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nama_brand = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    foto_sampul = models.ImageField(upload_to='sampul/', null=True, blank=True)
    deskripsi = models.TextField()
    telepon = models.CharField(max_length=20)
    email_bisnis = models.EmailField()
    alamat = models.TextField()

    def __str__(self):
        return f"Profil WO untuk {self.user.username} - {self.nama_brand}"

class GaleriWO(models.Model):
    profil_wo = models.ForeignKey(ProfilWO, related_name='galeri', on_delete=models.CASCADE)
    foto = models.ImageField(upload_to='galeri_wo/')

    def __str__(self):
        return f"Foto Galeri untuk {self.profil_wo.nama_brand}"