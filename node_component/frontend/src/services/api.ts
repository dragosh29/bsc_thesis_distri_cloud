// services/api.ts
import { FullNode, NodeConfig, TaskAssignment } from '../types/api';
import { localApiClient, hubApiClient } from './clients';



export async function fetchNodeConfig(): Promise<NodeConfig> {
  const { data } = await localApiClient.get('/node');
  return data;
}

export async function fetchTaskDetails(taskId: string, nodeId: string): Promise<TaskAssignment> {
  const { data } = await hubApiClient.get(`/tasks/${taskId}?node_id=${nodeId}`);
  return {
    id: data.id,
    description: data.description,
    started_at: data.assignment?.started_at || '',
    completed_at: data.assignment?.completed_at || undefined,
    status: data.assignment?.completed_at ? 'completed' : 'in_progress',
  };
}

export async function fetchFullNode(nodeId: string): Promise<FullNode> {
  const { data } = await hubApiClient.get(`/nodes/${nodeId}`);
  return {
    name: data.name,
    status: data.status,
    resourceCapacity: data.resources_capacity,
    resourceAvailable: data.free_resources,
    ipAddress: data.ip_address,
    trustIndex: data.trust_index,
  };
}

export async function registerNode(name: string): Promise<void> {
  await localApiClient.post('/node/register', { name });
}

export async function startNode(): Promise<void> {
  await localApiClient.post('/node/start');
}
