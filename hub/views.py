# views.py

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from hub.models import Node, Task, TaskAssignment
from hub.serializers import NodeSerializer, TaskSerializer


@api_view(['POST'])
def register_node(request):
    """
    Registers a new node in the system.
    """
    serializer = NodeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(['GET'])
def fetch_task(request):
    """
    In a push-based system using TaskAssignments:
      - A background job (TaskManager) moves tasks to 'in_progress' and creates
        TaskAssignment records for each node that should work on a task.
      - A node calls this endpoint to retrieve any uncompleted assignment it has.

    We'll just return the first uncompleted assignment's Task to the node.
    """
    node_id = request.query_params.get('node_id')
    if not node_id:
        return Response({"error": "Missing node_id parameter."}, status=400)

    try:
        node = Node.objects.get(id=node_id)
    except Node.DoesNotExist:
        return Response({"error": "Node not found."}, status=404)

    # Find the earliest assignment that isn't completed
    assignment = TaskAssignment.objects.filter(
        node=node,
        completed_at__isnull=True
    ).order_by('assigned_at').first()

    if not assignment:
        return Response({"message": "No assigned tasks available."}, status=404)

    # If you want to mark that the task started:
    assignment.started_at = timezone.now()
    assignment.save(update_fields=['started_at'])

    # Return the full Task to the node
    task_data = TaskSerializer(assignment.task).data
    return Response(task_data, status=200)


@api_view(['POST'])
def submit_task_result(request):
    """
    Endpoint for nodes to submit their results for a specific TaskAssignment.
    Looks up the TaskAssignment by (task_id, node_id).
    """
    task_id = request.data.get('task_id')
    node_id = request.data.get('node_id')
    result = request.data.get('result')

    if not (task_id and node_id and (result is not None)):
        return Response({"error": "task_id, node_id, and result are required fields."}, status=400)

    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({"error": "Task not found."}, status=404)

    try:
        assignment = TaskAssignment.objects.get(task=task, node_id=node_id)
    except TaskAssignment.DoesNotExist:
        return Response({"error": "TaskAssignment not found for the given node."}, status=404)

    # If already completed, no multiple submissions
    if assignment.completed_at:
        return Response({"error": "This TaskAssignment result was already submitted."}, status=400)

    # Record the result
    assignment.result = result
    assignment.validated = False  # Implement validation logic if needed
    assignment.completed_at = timezone.now()
    assignment.save()

    # Check if all assignments for this task are done
    total_assignments = TaskAssignment.objects.filter(task=task).count()
    completed_assignments = TaskAssignment.objects.filter(task=task, completed_at__isnull=False).count()

    # If all assigned nodes have completed, mark the Task as completed
    if completed_assignments == total_assignments:
        task.status = 'completed'
        task.save()

    return Response({"message": "Task result submitted successfully."}, status=200)


@api_view(['POST'])
def node_heartbeat(request):
    """
    Endpoint for nodes to send periodic heartbeats and resource usage updates.
    We do not mark nodes as failed; only tasks can fail.
    """
    node_id = request.data.get('node_id')
    resources_usage = request.data.get('resources_usage', {})

    if not node_id:
        return Response({"error": "node_id is required."}, status=400)

    try:
        node = Node.objects.get(id=node_id)
    except Node.DoesNotExist:
        return Response({"error": "Node not found."}, status=404)

    node.last_heartbeat = timezone.now()
    if isinstance(resources_usage, dict):
        node.resources_usage = resources_usage

    # Set the node status to active if it isn't already busy or something else
    # Adjust this logic according to your needs:
    if node.status != 'busy':
        node.status = 'active'

    node.save()
    return Response({"message": "Heartbeat received successfully."}, status=200)
