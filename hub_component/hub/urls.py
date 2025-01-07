from django.urls import path
from hub import views

urlpatterns = [
    path('nodes/register/', views.register_node, name='register_node'),
    path('tasks/fetch', views.fetch_task, name='fetch_task'),
    path('tasks/submit_result/', views.submit_task_result, name='submit_task_result'),
    path('nodes/heartbeat/', views.node_heartbeat, name='node_heartbeat'),
    path('tasks/submit_task/', views.submit_task, name='submit_task'),
    path('tasks', views.list_tasks, name='list'),
    path('nodes', views.list_nodes, name='list'),
]
