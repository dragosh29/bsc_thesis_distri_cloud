from rest_framework import serializers
from hub.models import Node, Task, TaskAssignment


class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = '__all__'

class NodeRegistrationSerializer(serializers.Serializer):
    """
    Serializer for node registration via API.
    """
    name = serializers.CharField(max_length=255, required=True)
    ip_address = serializers.IPAddressField(required=True)
    resources_capacity = serializers.JSONField(required=True)
    free_resources = serializers.JSONField(required=True)
    class Meta:
        model = Node
        fields = ['name', 'ip_address', 'resource_capacity', 'free_resources']

    def create(self, validated_data):
        """
        Create and return a new Node instance with default values for fields
        that are not included in the request.
        """
        return Node.objects.create(**validated_data)


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class TaskSubmissionSerializer(serializers.Serializer):
    """
    Serializer for task submission via API.
    """
    description = serializers.CharField(max_length=255, required=True)
    container_spec = serializers.JSONField(required=True)
    resource_requirements = serializers.JSONField(required=True)
    trust_index_required = serializers.FloatField(
        required=False, default=5.0,
        min_value=0.0, max_value=10.0
    )
    overlap_count = serializers.IntegerField(
        required=False, default=1,
        min_value=1
    )

    def validate_container_spec(self, value):
        """
        Ensure container_spec contains at least an 'image' field and a command field.
        """
        if 'image' not in value:
            raise serializers.ValidationError("Container spec must include an 'image' field.")
        if 'command' not in value:
            raise serializers.ValidationError("Container spec must include a 'command' field.")
        return value

    def validate_resource_requirements(self, value):
        """
        Ensure resource requirements contain 'cpu' and 'ram'.
        """
        if 'cpu' not in value or 'ram' not in value:
            raise serializers.ValidationError("Resource requirements must include 'cpu' and 'ram'.")
        return value