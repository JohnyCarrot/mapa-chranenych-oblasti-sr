"""bakalarka URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import path, include
from map import views as map_views
from django.conf.urls import include as include2



urlpatterns = [
    path('admin/', admin.site.urls),
    path('login',map_views.login_request),
    path("unicorn/", include("django_unicorn.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
    path('',map_views.index,name='index'),
    path('diskusia',map_views.forum,name='forum'),
    path('skupiny',map_views.skupiny_request,name='skupiny'),
    path('skupina',map_views.skupina_request,name='skupina'),
    path('test',map_views.test),
    path('bin',map_views.user_bin, name='bin'),
    path('profil',map_views.profil, name='profil'),
    path('mapa',map_views.render_mapy),
    path('mapa_cela',map_views.render_mapy_cela),
    path('api',map_views.api_request),
    path('api_file',map_views.api_request_file),
    path('administracia',map_views.administracia),
    path('administracia/json', map_views.administracia_json),
    path('administracia/bin', map_views.admin_bin),
    path('spravuj',map_views.subgroup_edit),
    path('accounts/',include('django.contrib.auth.urls'),name = "accounts"),
    path("register", map_views.register_request, name="register"),
    path('friendship/', include2('friendship.urls')),
    path("friends",map_views.friends_main_page,name="friends"),
    #path('__debug__/', include('debug_toolbar.urls')),
]

htmx_urlpatterns = [
    path('htmx/',map_views.htmx_request,name='zdielanie_list'),
]

urlpatterns+=htmx_urlpatterns
