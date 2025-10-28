"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# This bit is responsible for directing traffic to the right component
# all django applications have a urls.py, which then sends the request onwards
# to wherever it wishes
# see here about the different way of referencing component applications in django
# https://docs.djangoproject.com/en/5.2/ref/urls/
# https://docs.djangoproject.com/en/5.2/topics/http/urls/
urlpatterns = [
    # requests  for `/admin/` go to the built-in admin panel
    path('admin/', admin.site.urls),
    # requests for everything else go to the pdf_loader application
    #TODO: we probably want a landing  page or something like that for generic requests
    path('', include('pdf_loader.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
