"""YourAI_Project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.urls import path
from django.contrib.auth import views as auth_views

from YourAI import views

# errors handlers
handler404 = 'YourAI.views.handler404'
handler500 = 'YourAI.views.handler500'

urlpatterns = [
    path('admin/', admin.site.urls),

    # home dashboard page
    path(r'',views.home),
    # home dashboard page
    path(r'home',views.home),
    # free trial page
    path(r'trial',views.trialPage),
    # free trial detect emotion
    path(r'detectEmotionTrial',views.detectEmotionTrial),
    # data example page
    path(r'dataexamplePage',views.dataexamplePage),
    # upload file
    path(r'upload',views.uploadFile),
    # api description page
    path(r'apiPage',views.apiPage),
    # api url
    path(r'api',views.api),

    # register page
    path(r'registerPage',views.registerPage),
    # register
    path(r'register',views.register),
    # login page
    path(r'loginPage',views.loginPage),
    # http codes description
    path(r'httpcodesPage',views.httpDescription),


    # login page
    path(r'login',auth_views.LoginView.as_view(),name="login"),
    # logout
    path(r'logout', auth_views.LogoutView.as_view(), name='logout'),




]


