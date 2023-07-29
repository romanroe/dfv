from django.contrib import admin
from django.urls import include, path

# global URLs
urlpatterns = [
    # DFV Demos
    path("elements/", include("main.views.elements")),
    path("form/", include("main.views.form")),
    # Internal
    path("__adm__/", admin.site.urls),
    path("__debug__/", include("debug_toolbar.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
]
