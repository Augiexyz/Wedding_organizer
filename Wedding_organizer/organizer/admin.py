from django.contrib import admin
from .models import Paket, Pesanan, Gedung, FotoPortofolio

# Mendaftarkan Model agar muncul di Admin Panel
admin.site.register(Paket)
admin.site.register(Pesanan)
admin.site.register(Gedung)          # <--- TAMBAHKAN INI
admin.site.register(FotoPortofolio)  # Tambahkan ini juga agar bisa atur foto