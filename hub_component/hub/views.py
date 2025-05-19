import redis
from django.conf import settings
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from hub.models import Node, Task, TaskAssignment
from hub.serializers import NodeSerializer, TaskSerializer, NodeRegistrationSerializer
from hub.tasks import validate_docker_image_task


@api_view(['GET'])
def list_nodes(request):
    """
    List all nodes in the system.
    """
    nodes = Node.objects.all()
    serializer = NodeSerializer(nodes, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def fetch_node(request, node_id):
    """
    Get a specific node by ID.
    """
    try:
        node = Node.objects.get(id=node_id)
    except Node.DoesNotExist:
        return Response({"error": "Node not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = NodeSerializer(node)
    return Response(serializer.data)

@api_view(['GET'])
def list_tasks(request):
    """
    List all tasks in the system.
    """
    tasks = Task.objects.all()
    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def register_node(request):
    """
    Registers a new node in the system.
    """
    req_serializer = NodeRegistrationSerializer(data=request.data)
    if req_serializer.is_valid():
        node = req_serializer.save()
        res_serializer = NodeSerializer(node)
        return Response(res_serializer.data, status=status.HTTP_201_CREATED)
    return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

    assignment = TaskAssignment.objects.filter(
        node=node,
        completed_at__isnull=True
    ).order_by('assigned_at').first()

    if not assignment:
        return Response({"message": "No assigned tasks available."}, status=status.HTTP_404_NOT_FOUND)

    assignment.started_at = timezone.now()
    assignment.save(update_fields=['started_at'])

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

    assignment.result = result
    assignment.completed_at = timezone.now()
    assignment.save()

    assignments = TaskAssignment.objects.filter(task_id=task_id)
    if all(a.completed_at is not None for a in assignments):
        task = Task.objects.get(id=task_id)
        task.status = 'completed'
        task.save()
        from hub.task_manager import TaskManager
        manager = TaskManager()
        manager.validate_task(task_id)

    print(f"[SUBMIT TASK RESULT] Task {task_id} result: {result}")
    return Response({"message": "Task result submitted successfully."}, status=status.HTTP_200_OK)


@api_view(['POST'])
def node_heartbeat(request):
    """
    Endpoint for nodes to send periodic heartbeats and resource availability updates.
    We do not mark nodes as failed; only tasks can fail.
    """
    node_id = request.data.get('node_id')
    free_resources = request.data.get('free_resources')

    if not node_id:
        return Response({"error": "node_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        node = Node.objects.get(id=node_id)
    except Node.DoesNotExist:
        return Response({"error": "Node not found."}, status=status.HTTP_404_NOT_FOUND)

    node.last_heartbeat = timezone.now()
    if isinstance(free_resources, dict):
        node.free_resources = free_resources

    if node.status != 'busy':
        node.status = 'active'

    node.save()
    return Response({"message": "Heartbeat received successfully."}, status=status.HTTP_200_OK)


@api_view(['POST'])
def submit_task(request):
    """
    Submit a task and queue it for Docker image validation.
    """
    submitted_by = request.data.get('submitted_by')
    if not submitted_by:
        return Response({"error": "submitted_by is required. Only registered nodes can submit."}, status=status.HTTP_400_BAD_REQUEST)
    node = None
    try:
        node = Node.objects.get(id=submitted_by)
    except Node.DoesNotExist:
        return Response({"error": "Node not found."}, status=status.HTTP_404_NOT_FOUND)

    description = request.data.get('description')
    container_spec = request.data.get('container_spec', {})
    resource_requirements = request.data.get('resource_requirements', {})
    trust_index_required = request.data.get('trust_index_required', 5.0)
    overlap_count = request.data.get('overlap_count', 1)

    if not (description and container_spec.get('image') and container_spec.get('command')):
        return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

    task = Task.objects.create(
        description=description,
        container_spec=container_spec,
        resource_requirements=resource_requirements,
        trust_index_required=trust_index_required,
        overlap_count=overlap_count,
        status='validating',
        submitted_by=node
    )

    validate_docker_image_task.apply_async(args=[str(task.id)])

    return Response({"message": "Task submitted and queued for validation", "task_id": str(task.id)}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_task(request, task_id):
    """
    Get task details by ID.
    If a node_id is provided as query param, include assignment context for that node.
    """
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({"error": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

    data = TaskSerializer(task).data

    node_id = request.query_params.get("node_id")
    if node_id:
        try:
            assignment = TaskAssignment.objects.get(task_id=task_id, node_id=node_id)
            data["assignment"] = {
                "node_id": node_id,
                "started_at": assignment.started_at,
                "completed_at": assignment.completed_at,
                "result": assignment.result
            }
        except TaskAssignment.DoesNotExist:
            data["assignment"] = {
                "node_id": node_id,
                "message": "No assignment found for this node."
            }

    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_submitted_tasks(request):
    """
    Get all tasks submitted by a specific node.
    """
    node_id = request.query_params.get('node_id')
    if not node_id:
        return Response({"error": "node_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        node = Node.objects.get(id=node_id)
    except Node.DoesNotExist:
        return Response({"error": "Node not found."}, status=status.HTTP_404_NOT_FOUND)

    tasks = Task.objects.filter(submitted_by=node)
    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


def network_activity_stream():
    redis_client = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL)
    pubsub = redis_client.pubsub()
    pubsub.subscribe(settings.REDIS_NETWORK_ACTIVITY_CHANNEL)

    try:
        for message in pubsub.listen():
            if message["type"] == "message":
                yield f"data: {message['data'].decode('utf-8')}\n\n"
    except GeneratorExit:
        pubsub.close()


def task_update_stream(node_id):
    redis_client = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL)
    pubsub = redis_client.pubsub()
    channel = settings.REDIS_TASK_UPDATES_CHANNEL
    pubsub.subscribe(channel)

    try:
        for message in pubsub.listen():
            if message["type"] == "message":
                yield f"data: {message['data'].decode('utf-8')}\n\n"
    except GeneratorExit:
        pubsub.close()


def sse_network_activity(request):
    response = StreamingHttpResponse(network_activity_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


def sse_task_updates(request):
    node_id = request.GET.get('node_id')
    if not node_id:
        return Response({"error": "node_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    response = StreamingHttpResponse(task_update_stream(node_id), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    return response
