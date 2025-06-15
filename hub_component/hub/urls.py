from django.urls import path
from hub import views

urlpatterns = [
    path('nodes/register/', views.register_node, name='register_node'),
    path('tasks/fetch', views.fetch_task, name='fetch_task'),
    path('tasks/submit_result/', views.submit_task_result, name='submit_task_result'),
    path('nodes/heartbeat/', views.node_heartbeat, name='node_heartbeat'),
    path('tasks/submit_task/', views.submit_task, name='submit_task'),
    path('tasks', views.list_tasks, name='list_tasks'),
    path('nodes', views.list_nodes, name='list_nodes'),
    path('nodes/<uuid:node_id>', views.fetch_node, name='fetch_node'),
    path('tasks/<uuid:task_id>/', views.get_task, name='get_task'),
    path('tasks/submitted_tasks', views.get_submitted_tasks, name='get_submitted_tasks'),
    path('network_activity/', views.network_activity, name='network_activity'),
    path('sse/network_activity/', views.sse_network_activity, name='sse_network_activity'),
    path('sse/task_updates/', views.sse_task_updates, name='sse_task_updates'),
    path('experiment/trust_validation/setup/', views.validation_experiment_setup, name='trust_validation_setup'),
    path('experiment/trust_validation/keep_alive/', views.validation_experiment_keep_nodes_alive, name='trust_validation_keep_alive'),
    path('experiment/distribution/trigger_orchestration/', views.distribution_experiment_trigger_orchestration, name='distribution_experiment_trigger_orchestration'),
    path('experiment/distribution/create_node/', views.distribution_experiment_create_node, name='distribution_experiment_create_node'),
    path('experiment/distribution/reset_db/', views.distribution_experiment_reset_db, name='distribution_experiment_reset_db'),
]
