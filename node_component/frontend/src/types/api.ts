export interface TaskAssignment {
    id: string;
    description: string;
    started_at: string;
    completed_at?: string;
    status: string;
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