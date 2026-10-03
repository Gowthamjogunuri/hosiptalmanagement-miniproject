"""Patient URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import FileResponse, Http404
from django.conf import settings
from pathlib import Path


def serve_report(request, filename):
    report_path = (settings.MEDIA_ROOT / filename).resolve()
    try:
        report_path.relative_to(settings.MEDIA_ROOT.resolve())
    except ValueError:
        raise Http404

    try:
        return FileResponse(report_path.open("rb"))
    except FileNotFoundError:
        raise Http404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('PatientApp.urls')),
    re_path(r'^media/(?P<filename>.+)$', serve_report, name='serve-report'),
]
