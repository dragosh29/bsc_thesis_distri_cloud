import pytest
from hub.models import Node
from hub.tests.factories import NodeFactory


@pytest.mark.django_db
def test_node_factory_creates_valid_node():
    """Sanity check"""
    node = NodeFactory()
    assert isinstance(node, Node)
    assert node.status == "active"
    assert "cpu" in node.resources_capacity