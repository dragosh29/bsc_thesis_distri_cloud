from django.contrib import admin
from .models import Node, Task, TaskAssignment, Heartbeat

@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'ip_address', 'status', 'trust_index', 'last_heartbeat')
    list_filter = ('status',)
    search_fields = ('name', 'ip_address')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'status',
                    'trust_index_required', 'overlap_count', 'created_at', 'updated_at', 'get_assigned_nodes')

@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'node', 'validated', 'assigned_at', 'completed_at')

@admin.register(Heartbeat)
class HeartbeatAdmin(admin.ModelAdmin):
    list_display = ('id', 'node', 'timestamp', 'status')
