# organizer/admin.py

from django.contrib import admin
from .models import Paket, Pesanan

admin.site.register(Paket)
admin.site.register(Pesanan)