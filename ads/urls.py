from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'ads', views.AdViewSet)
router.register(r'proposals', views.ExchangeProposalViewSet)

urlpatterns = [
    # Веб-интерфейс
    path('', views.ad_list, name='ad_list'),
    path('my-ads/', views.my_ads, name='my_ads'),
    path('ad/<int:pk>/', views.ad_detail, name='ad_detail'),
    path('ad/create/', views.ad_create, name='ad_create'),
    path('ad/<int:pk>/edit/', views.ad_edit, name='ad_edit'),
    path('ad/<int:pk>/delete/', views.ad_delete, name='ad_delete'),
    path('ad/<int:ad_id>/propose/', views.proposal_create, name='proposal_create'),
    path('proposals/', views.proposal_list, name='proposal_list'),
    path('proposal/<int:pk>/update/', views.proposal_update_status, name='proposal_update_status'),
    
    # API
    path('api/', include(router.urls)),
]
