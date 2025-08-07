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
    
    # Управление родителями
    path('parent-management/', views.parent_management, name='parent_management'),
    path('parent/create/', views.create_parent, name='create_parent'),
    path('parent/<int:parent_id>/edit/', views.edit_parent, name='edit_parent'),
    path('parent/<int:parent_id>/delete/', views.delete_parent, name='delete_parent'),
    path('parent/link-student/', views.link_student_parent, name='link_student_parent'),
    path('student/<int:student_id>/unlink-parent/', views.unlink_student_parent, name='unlink_student_parent'),
    path('api/parent/<int:parent_id>/', views.get_parent_data, name='get_parent_data'),
    
    # Управление школьной системой
    path('city-management/', views.city_management, name='city_management'),
    path('city/create/', views.create_city, name='create_city'),
    path('school-management/', views.school_management, name='school_management'),
    path('school/create/', views.create_school, name='create_school'),
    path('school/<int:school_id>/', views.school_detail, name='school_detail'),
    path('school/<int:school_id>/course/create/', views.create_course, name='create_course'),
    path('course/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('course/<int:course_id>/delete/', views.delete_course, name='delete_course'),
    path('api/school/<int:school_id>/courses/', views.get_courses_by_school, name='get_courses_by_school'),
    path('api/group/<int:group_id>/students/', views.get_group_students, name='get_group_students'),
    
    # Страницы футера
    path('institutions/', views.institutions, name='institutions'),
    path('return-policy/', views.return_policy, name='return_policy'),
    path('data-transfer/', views.data_transfer, name='data_transfer'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('support/', views.support, name='support'),
    path('astrocoins-program/', views.astrocoins_program, name='astrocoins_program'),
    path('changelog/', views.changelog, name='changelog'),
]