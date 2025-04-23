// hooks/useNodeData.ts
import { useEffect, useReducer, useState, useRef } from 'react';
import {
  fetchFullNode,
  fetchTaskDetails,
  fetchNodeConfig,
  registerNode,
  startNode,
} from '../services/api';
import { FullNode, NodeConfig, TaskAssignment } from '../types/api';



interface State {
  nodeConfig: NodeConfig | null;
  fullNode: FullNode | null;
}

type Action =
  | { type: 'SET_NODE_CONFIG'; payload: NodeConfig }
  | { type: 'SET_LAST_TASK'; payload: TaskAssignment }
  | { type: 'SET_FULL_NODE'; payload: FullNode };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_NODE_CONFIG': {
      const existingTask =
        state.nodeConfig?.last_task_id === action.payload.last_task_id
          ? state.nodeConfig?.last_task
          : undefined;
      return {
        ...state,
        nodeConfig: {
          ...action.payload,
          last_task: existingTask,
        },
      };
    }
    case 'SET_LAST_TASK': {
      if (!state.nodeConfig) return state;
      return {
        ...state,
        nodeConfig: {
          ...state.nodeConfig,
          last_task: action.payload,
        },
      };
    }
    case 'SET_FULL_NODE': {
      return { ...state, fullNode: action.payload };
    }
    default:
      return state;
  }
}

export function useNodeData() {
  const [state, dispatch] = useReducer(reducer, {
    nodeConfig: null,
    fullNode: null,
  });
  const [isRegistering, setIsRegistering] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const lastTaskIdRef = useRef<string | null>(null);

  const fetchLastTaskDetails = async (taskId: string, nodeId: string) => {
    if (lastTaskIdRef.current === taskId) return;
    lastTaskIdRef.current = taskId;

    const task = await fetchTaskDetails(taskId, nodeId);
    dispatch({ type: 'SET_LAST_TASK', payload: task });
  };

  const fetchNodeStatus = async () => {
    const config = await fetchNodeConfig();
    dispatch({ type: 'SET_NODE_CONFIG', payload: config });

    if (config.node_id) {
      const fullNode = await fetchFullNode(config.node_id);
      dispatch({ type: 'SET_FULL_NODE', payload: fullNode });

      if (config.last_task_id) {
        await fetchLastTaskDetails(config.last_task_id, config.node_id);
      }
    }
  };

  const handleRegisterNode = async (name: string) => {
    setIsRegistering(true);
    await registerNode(name);
    await fetchNodeStatus();
    setIsRegistering(false);
  };

  const handleStartNode = async () => {
    setIsStarting(true);
    await startNode();
    await fetchNodeStatus();
    setIsStarting(false);
  };

  useEffect(() => {
    fetchNodeStatus();
    const interval = setInterval(fetchNodeStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  return {
    nodeConfig: state.nodeConfig,
    fullNode: state.fullNode,
    isRegistering,
    isStarting,
    handleRegisterNode,
    handleStartNode,
  };
}
