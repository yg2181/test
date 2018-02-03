from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^getmeal/$', views.get_meal, name='get_meal')
]
