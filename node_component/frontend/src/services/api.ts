import { FullNode, NetworkActivityData, NodeConfig, Task, TaskAssignment } from '../types/api';
import { localApiClient, hubApiClient, sseClient } from './clients';
import { SubmitTaskPayload } from '../types/api';


const DEBOUNCE_DELAY = 3000;

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

export async function stopNode(): Promise<void> {
  await localApiClient.post('/node/stop');
}

export async function submitTask(payload: SubmitTaskPayload): Promise<void> {
  await hubApiClient.post('/tasks/submit_task/', payload);
  console.log('Task submitted:', payload);
}

export async function fetchSubmittedTasks(node_id: string): Promise<Task[]> {
  const { data } = await hubApiClient.get(`/tasks/submitted_tasks?node_id=${node_id}`);
  return data.map((task: Task) => ({
    id: task.id,
    description: task.description,
    created_at: task.created_at,
    updated_at: task.updated_at,
    status: task.status,
    container_spec: task.container_spec,
    resource_requirements: task.resource_requirements,
    trust_index_required: task.trust_index_required,
    overlap_count: task.overlap_count,
    result: task.result,
  }));
}

export async function fetchNetworkActivity(): Promise<NetworkActivityData> {
  const { data } = await hubApiClient.get('/network_activity');
  return data.data;
}

export const subscribeToNetworkActivity = (
  onData: (data: NetworkActivityData) => void,
  onError?: (error: Event) => void
): (() => void) => {
  const sse = sseClient.getEventSource('/sse/network_activity/');
  let debounceTimeout: NodeJS.Timeout | null = null;

  sse.onmessage = (event: MessageEvent) => {
    const parsedData = JSON.parse(event.data);
    if (parsedData.type === 'network_activity') {
      if (debounceTimeout) clearTimeout(debounceTimeout);
      debounceTimeout = setTimeout(() => {
        onData(parsedData.data);
      }, DEBOUNCE_DELAY);
    }
  };

  sse.onerror = (error) => {
    if (onError) onError(error);
    sse.close();
  };

  return () => {
    if (debounceTimeout) clearTimeout(debounceTimeout);
    sse.close();
  };
};

export const subscribeToSubmittedTaskUpdates = (
  nodeId: string,
  onRefetchSignal: () => void,
  onError?: (error: Event) => void
): (() => void) => {
  const sse = sseClient.getEventSource(`/sse/task_updates/?node_id=${nodeId}`);
  
  sse.onmessage = (event: MessageEvent) => {
    const parsed = JSON.parse(event.data);
    if (parsed.type === 'task_update' && parsed.node_id === nodeId && parsed.action === 'refetch') {
      onRefetchSignal();
    }
  };

  sse.onerror = (error) => {
    if (onError) onError(error);
    sse.close();
  };

  return () => {
    sse.close();
  };
};