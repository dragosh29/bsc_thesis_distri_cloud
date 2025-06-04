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
    path('nodes/<uuid:node_id>', views.fetch_node, name='fetch_node'),
    path('tasks/<uuid:task_id>/', views.get_task, name='get_task'),
    path('tasks/submitted_tasks', views.get_submitted_tasks, name='get_submitted_tasks'),
    path('network_activity/', views.network_activity, name='network_activity'),
    path('sse/network_activity/', views.sse_network_activity, name='sse_network_activity'),
    path('sse/task_updates/', views.sse_task_updates, name='sse_task_updates'),
]
