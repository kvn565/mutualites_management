# aide/urls.py
from django.urls import path
from . import views

app_name = 'aide'

urlpatterns = [
    # Aide locale (mutualité)
    path('', views.AideIndexView.as_view(), name='index'),
    path('categorie/<int:pk>/', views.CategorieAideDetailView.as_view(), name='categorie'),
    path('article/<slug:slug>/', views.ArticleAideDetailView.as_view(), name='article'),
    path('recherche/', views.recherche_aide, name='recherche'),

    # Messages mutualité → SuperAdmin
    path('messages/', views.MessageSuperAdminListView.as_view(), name='message_list'),
    path('messages/nouveau/', views.MessageSuperAdminCreateView.as_view(), name='message_create'),
    path('messages/<int:pk>/', views.MessageSuperAdminDetailView.as_view(), name='message_detail'),

    # SuperAdmin : Gestion messages
    path('superadmin/messages/', views.SuperAdminMessageListView.as_view(), name='superadmin_message_list'),
    path('superadmin/messages/<int:pk>/', views.SuperAdminMessageDetailView.as_view(), name='superadmin_message_detail'),
    path('superadmin/messages/<int:pk>/repondre/', views.superadmin_message_repondre, name='superadmin_message_repondre'),
    path('superadmin/messages/<int:pk>/statut/', views.superadmin_message_changer_statut, name='superadmin_message_changer_statut'),

    # SuperAdmin : Documents (Doc/Guide/FAQ)
    path('superadmin/documents/', views.SuperAdminDocumentListView.as_view(), name='superadmin_document_list'),
    path('superadmin/documents/nouveau/', views.SuperAdminDocumentCreateView.as_view(), name='superadmin_document_create'),
    path('superadmin/documents/<int:pk>/modifier/', views.SuperAdminDocumentUpdateView.as_view(), name='superadmin_document_update'),
    path('superadmin/documents/<int:pk>/supprimer/', views.SuperAdminDocumentDeleteView.as_view(), name='superadmin_document_delete'),

    # SuperAdmin : visualisation des documents publiés
    path('superadmin/documents-publies/', views.SuperAdminDocumentPublicListView.as_view(), name='superadmin_doc_list'),
    path('superadmin/documents-publies/<slug:slug>/', views.SuperAdminDocumentPublicDetailView.as_view(), name='superadmin_doc_detail'),

    # Public (toutes mutualités) : Documents SuperAdmin
    path('documents/', views.DocumentSuperAdminPublicListView.as_view(), name='doc_superadmin_list'),
    path('documents/<slug:slug>/', views.DocumentSuperAdminPublicDetailView.as_view(), name='doc_superadmin_detail'),
]