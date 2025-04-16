from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def redirect_to_home(request):
    return redirect('/home/')  # Redirect root path to /home/

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', include('time_table.urls')),
    path('', redirect_to_home),  # Add this line to redirect root
]
