from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from hub.models import Node, Task, TaskAssignment
from hub.serializers import NodeSerializer, TaskSerializer

@api_view(['POST'])
def register_node(request):
    serializer = NodeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
def fetch_task(request):
    node_id = request.query_params.get('node_id')
    try:
        node = Node.objects.get(id=node_id)
        task = Task.objects.filter(status='pending').first()
        if task:
            task.status = 'in_progress'
            task.assigned_node = node
            task.save()
            return Response(TaskSerializer(task).data)
        return Response({"message": "No tasks available"}, status=404)
    except Node.DoesNotExist:
        return Response({"error": "Node not found"}, status=404)


@api_view(['POST'])
def submit_task_result(request):
    """
    Endpoint for nodes to submit task results.
    """
    task_id = request.data.get('task_id')
    node_id = request.data.get('node_id')
    result = request.data.get('result')

    if not task_id or not node_id or result is None:
        return Response({"error": "task_id, node_id, and result are required fields."}, status=400)

    try:
        task = Task.objects.get(id=task_id)
        assignment = TaskAssignment.objects.get(task=task, node_id=node_id)

        if assignment.completed_at:
            return Response({"error": "Task result already submitted."}, status=400)

        # Update task assignment with result and completion timestamp
        assignment.result = result
        assignment.validated = False  # Validation logic can be added later
        assignment.completed_at = timezone.now()
        assignment.save()

        # Optionally update task status
        if TaskAssignment.objects.filter(task=task, validated=False).count() == 0:
            task.status = 'completed'
            task.save()

        return Response({"message": "Task result submitted successfully."}, status=200)

    except Task.DoesNotExist:
        return Response({"error": "Task not found."}, status=404)
    except TaskAssignment.DoesNotExist:
        return Response({"error": "TaskAssignment not found for the given node."}, status=404)


@api_view(['POST'])
def node_heartbeat(request):
    """
    Endpoint for nodes to send periodic heartbeats.
    """
    node_id = request.data.get('node_id')
    resources_usage = request.data.get('resources_usage', {})

    if not node_id:
        return Response({"error": "node_id is required."}, status=400)

    try:
        node = Node.objects.get(id=node_id)

        # Update node's last heartbeat and resources usage
        node.last_heartbeat = timezone.now()
        if isinstance(resources_usage, dict):
            node.resources_usage = resources_usage
        node.status = 'active'
        node.save()

        return Response({"message": "Heartbeat received successfully."}, status=200)

    except Node.DoesNotExist:
        return Response({"error": "Node not found."}, status=404)
