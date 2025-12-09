# Wedding_organizer/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# HANYA PERLU URL PATTERNS INI
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('beranda.urls')),       # Mengarahkan ke aplikasi beranda
    path('akun/', include('pengguna.urls')),    # Mengarahkan ke aplikasi pengguna
    path('organizer/', include('organizer.urls')),
]

# Bagian untuk media files tetap di sini
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
