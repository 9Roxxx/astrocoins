from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('shop/', views.shop, name='shop'),
    path('shop/add/', views.add_product, name='add_product'),
    path('shop/edit/', views.edit_product, name='edit_product'),
    path('shop/category/add/', views.add_category, name='add_category'),
    path('shop/category/edit/', views.edit_category, name='edit_category'),
    path('shop/category/delete/', views.delete_category, name='delete_category'),
    path('api/product/<int:product_id>/', views.get_product, name='get_product'),
    path('api/category/<int:category_id>/', views.get_category, name='get_category'),
    path('api/product/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('purchase/<int:product_id>/', views.purchase_product, name='purchase_product'),
    path('transfer/', views.transfer_coins, name='transfer_coins'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<int:user_id>/edit/', views.profile_edit, name='profile_edit_user'),
    path('knowledge-base/', views.knowledge_base, name='knowledge_base'),
    path('groups/', views.groups, name='groups'),
    path('news/', views.news, name='news'),
    path('activity-monitoring/', views.activity_monitoring, name='activity_monitoring'),
    path('user-management/', views.user_management, name='user_management'),
    path('student/<int:student_id>/coins/', views.manage_coins, name='manage_coins'),
    path('student/<int:student_id>/profile/', views.student_profile, name='student_profile'),
    
    # Страницы футера
    path('institutions/', views.institutions, name='institutions'),
    path('return-policy/', views.return_policy, name='return_policy'),
    path('data-transfer/', views.data_transfer, name='data_transfer'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('support/', views.support, name='support'),
    path('astrocoins-program/', views.astrocoins_program, name='astrocoins_program'),
    path('changelog/', views.changelog, name='changelog'),
]