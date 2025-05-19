export interface TaskAssignment {
    id: string;
    description: string;
    started_at: string;
    completed_at?: string;
    status: string;
}

export interface Task {
    id: string;
    status: string;
    created_at: string;
    updated_at?: string;
    result?: {
      trust_score?: number;
      validated_output?: string;
      error?: string;
    };
    description: string;
    container_spec: {
      image: string;
      command: string;
    };
    resource_requirements: {
      cpu: number;
      ram: number;
    };
    trust_index_required?: number;
    overlap_count?: number;
}

export interface ResourceUsage {
    cpu: number;
    ram: number;
}

export interface NodeConfig {
    node_id?: string;
    status: string;
    is_running?: boolean;
    last_task_id?: string;
    last_task?: TaskAssignment;
    resource_usage?: ResourceUsage;
}

export interface FullNode {
    name: string;
    status: string;
    resourceCapacity: { cpu: number; ram: number };
    resourceAvailable: { cpu: number; ram: number };
    ipAddress: string;
    trustIndex: number;
}

export interface SubmitTaskPayload {
    description: string;
    container_spec: {
      image: string;
      command: string;
    };
    resource_requirements: {
      cpu: number;
      ram: number;
    };
    trust_index_required?: number;
    overlap_count?: number;
    submitted_by: string;
  }
  
  export interface NetworkActivityData {
    active_nodes: number;
    total_cpu: number;
    total_ram: number;
    pending_tasks: number;
    in_queue_tasks: number;
    in_progress_tasks: number;
    completed_tasks: number;
    validated_tasks: number;
    failed_tasks: number;
    average_trust_index: number;
  }
  