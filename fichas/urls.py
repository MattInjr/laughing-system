from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),

    # Fichas
    path('criar/', views.criar_ficha, name='criar_ficha'),
    path('ficha/<int:id>/', views.editar_ficha, name='editar_ficha'),
    path('autosave/<int:id>/', views.autosave_ficha, name='autosave'),
    path('deletar/<int:id>/', views.deletar_ficha, name='deletar_ficha'),
    path('rolar/<int:id>/', views.rolar_dados, name='rolar_dados'),

    # Inventário
    path('ficha/<int:ficha_id>/item/adicionar/', views.adicionar_item, name='adicionar_item'),
    path('item/<int:item_id>/editar/', views.editar_item, name='editar_item'),
    path('item/<int:item_id>/deletar/', views.deletar_item, name='deletar_item'),

    # Campanhas
    path('campanha/criar/', views.criar_campanha, name='criar_campanha'),
    path('campanha/<int:id>/', views.ver_campanha, name='ver_campanha'),
    path('campanha/<int:id>/entrar/', views.entrar_campanha, name='entrar_campanha'),
    path('campanha/<int:id>/sair/', views.sair_campanha, name='sair_campanha'),
    path('campanha/<int:id>/deletar/', views.deletar_campanha, name='deletar_campanha'),
    path('campanha/<int:id>/escudo/', views.escudo_api, name='escudo_api'),

    # Bestiário
    path('campanha/<int:campanha_id>/criatura/criar/', views.criar_criatura, name='criar_criatura'),
    path('criatura/<int:criatura_id>/deletar/', views.deletar_criatura, name='deletar_criatura'),

    # Combate
    path('campanha/<int:campanha_id>/combate/iniciar/', views.iniciar_combate, name='iniciar_combate'),
    path('combate/<int:combate_id>/api/', views.combate_api, name='combate_api'),
    path('combate/<int:combate_id>/acao/', views.acao_combate, name='acao_combate'),
]