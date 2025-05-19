from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from hub.models import Node, Task
from hub.redis_publisher import publish_network_activity, publish_task_update


@receiver(pre_save, sender=Node)
def cache_old_node_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Node.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Node.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Node)
def emit_network_activity_on_node_update(sender, instance, created, **kwargs):
    if created or instance._old_status != instance.status:
        publish_network_activity()

@receiver(pre_save, sender=Task)
def cache_old_task_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Task.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Task.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Task)
def emit_network_activity_on_task_update(sender, instance, created, **kwargs):
    if created or instance._old_status != instance.status:
        publish_network_activity()
        if instance.submitted_by:
            publish_task_update(instance.submitted_by.id, emit=True)
