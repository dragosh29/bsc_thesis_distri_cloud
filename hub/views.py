# views.py

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from hub.models import Node, Task, TaskAssignment
from hub.serializers import NodeSerializer, TaskSerializer, TaskSubmissionSerializer
from hub.tasks import validate_docker_image_task


@api_view(['POST'])
def register_node(request):
    """
    Registers a new node in the system.
    """
    serializer = NodeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        return Response({"error": "Missing node_id parameter."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        node = Node.objects.get(id=node_id)
    except Node.DoesNotExist:
        return Response({"error": "Node not found."}, status=status.HTTP_404_NOT_FOUND)

    # Find the earliest assignment that isn't completed
    assignment = TaskAssignment.objects.filter(
        node=node,
        completed_at__isnull=True
    ).order_by('assigned_at').first()

    if not assignment:
        return Response({"message": "No assigned tasks available."}, status=status.HTTP_404_NOT_FOUND)

    # If you want to mark that the task started:
    assignment.started_at = timezone.now()
    assignment.save(update_fields=['started_at'])

    # Return the full Task to the node
    task_data = TaskSerializer(assignment.task).data
    return Response(task_data, status=status.HTTP_200_OK)


@api_view(['POST'])
def submit_task_result(request):
    """
    Endpoint for nodes to submit their results for a specific TaskAssignment.
    Looks up the TaskAssignment by (task_id, node_id).
    """
    task_id = request.data.get('task_id')
    node_id = request.data.get('node_id')
    result = request.data.get('result')

    if not (task_id and node_id and result):
        return Response({"error": "task_id, node_id, and result are required fields."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        assignment = TaskAssignment.objects.get(task_id=task_id, node_id=node_id)
    except TaskAssignment.DoesNotExist:
        return Response({"error": "TaskAssignment not found for the given node."}, status=status.HTTP_404_NOT_FOUND)

    if assignment.completed_at:
        return Response({"error": "This TaskAssignment result was already submitted."}, status=status.HTTP_400_BAD_REQUEST)

    # Save result
    assignment.result = result
    assignment.completed_at = timezone.now()
    assignment.save()

    # Check if all assignments are completed
    total_assignments = TaskAssignment.objects.filter(task_id=task_id).count()
    completed_assignments = TaskAssignment.objects.filter(task_id=task_id, completed_at__isnull=False).count()

    if completed_assignments == total_assignments:
        assignment.task.status = 'completed'
        assignment.task.save()

        # Trigger Validation
        from hub.task_manager import TaskManager
        manager = TaskManager()
        manager.validate_task(task_id)

    print(f"[SUBMIT TASK RESULT] Task {task_id} result: {result}")
    return Response({"message": "Task result submitted successfully."}, status=status.HTTP_200_OK)


@api_view(['POST'])
def node_heartbeat(request):
    """
    Endpoint for nodes to send periodic heartbeats and resource usage updates.
    We do not mark nodes as failed; only tasks can fail.
    """
    node_id = request.data.get('node_id')
    resources_usage = request.data.get('resources_usage', {})

    if not node_id:
        return Response({"error": "node_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        node = Node.objects.get(id=node_id)
    except Node.DoesNotExist:
        return Response({"error": "Node not found."}, status=status.HTTP_404_NOT_FOUND)

    node.last_heartbeat = timezone.now()
    if isinstance(resources_usage, dict):
        node.resources_usage = resources_usage

    # Set the node status to active if it isn't already busy or something else
    # Adjust this logic according to your needs:
    if node.status != 'busy':
        node.status = 'active'

    node.save()
    return Response({"message": "Heartbeat received successfully."}, status=status.HTTP_200_OK)


@api_view(['POST'])
def submit_task(request):
    """
    Submit a task and queue it for Docker image validation.
    """
    description = request.data.get('description')
    container_spec = request.data.get('container_spec', {})
    resource_requirements = request.data.get('resource_requirements', {})
    trust_index_required = request.data.get('trust_index_required', 5.0)
    overlap_count = request.data.get('overlap_count', 1)

    if not (description and container_spec.get('image') and container_spec.get('command')):
        return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

    # Create a task in 'validating' state
    task = Task.objects.create(
        description=description,
        container_spec=container_spec,
        resource_requirements=resource_requirements,
        trust_index_required=trust_index_required,
        overlap_count=overlap_count,
        status='validating'
    )

    # Trigger Docker image validation
    validate_docker_image_task.apply_async(args=[str(task.id)])

    return Response({"message": "Task submitted and queued for validation", "task_id": str(task.id)}, status=status.HTTP_201_CREATED)