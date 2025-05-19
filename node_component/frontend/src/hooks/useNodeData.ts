import { useEffect, useReducer, useState, useRef, useMemo } from 'react';
import {
  fetchFullNode,
  fetchTaskDetails,
  fetchNodeConfig,
  registerNode,
  startNode,
  stopNode,
} from '../services/api';
import { FullNode, NodeConfig, TaskAssignment } from '../types/api';
import { shallowEqualExcept } from '../utils/equality';

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
      const existing = state.nodeConfig;
      const incoming = action.payload;

      if (
        existing &&
        shallowEqualExcept(existing, incoming, ['resource_usage', 'last_task']) &&
        existing.last_task_id === incoming.last_task_id
      ) {
        return state;
      }

      let preservedTask: TaskAssignment | undefined = undefined;
      if (existing && existing.last_task_id === incoming.last_task_id) {
        preservedTask = existing.last_task;
      }

      return {
        ...state,
        nodeConfig: {
          ...incoming,
          last_task: preservedTask,
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
      const existing = state.fullNode;
      const incoming = action.payload;

      if (existing && shallowEqualExcept(existing, incoming, ['resourceAvailable'])) {
        return state;
      }

      return { ...state, fullNode: incoming };
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
  const [isStopping, setIsStopping] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const lastTaskIdRef = useRef<string | null>(null);

  const fetchLastTaskDetails = async (taskId: string, nodeId: string) => {
    if (lastTaskIdRef.current === taskId) return;
    lastTaskIdRef.current = taskId;

    const task = await fetchTaskDetails(taskId, nodeId);
    dispatch({ type: 'SET_LAST_TASK', payload: task });
  };

  const fetchNodeStatus = async () => {
    try {
      setIsLoading(true);
      const config = await fetchNodeConfig();
      dispatch({ type: 'SET_NODE_CONFIG', payload: config });

      if (config.node_id) {
        const fullNode = await fetchFullNode(config.node_id);
        dispatch({ type: 'SET_FULL_NODE', payload: fullNode });

        if (config.last_task_id) {
          await fetchLastTaskDetails(config.last_task_id, config.node_id);
        }
      }
    } finally {
      setIsLoading(false);
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

  const handleStopNode = async () => {
    setIsStopping(true);
    await stopNode();
    await fetchNodeStatus();
    setIsStopping(false);
  };

  useEffect(() => {
    fetchNodeStatus();
    const interval = setInterval(fetchNodeStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  return useMemo(() => ({
    nodeConfig: state.nodeConfig,
    fullNode: state.fullNode,
    isRegistering,
    isStarting,
    isStopping,
    isLoading,
    handleRegisterNode,
    handleStartNode,
    handleStopNode,
  }), [
    state.nodeConfig,
    state.fullNode,
    isRegistering,
    isStarting,
    isStopping,
    isLoading
  ]);
}
