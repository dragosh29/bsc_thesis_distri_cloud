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

  /*
    * Reducer function to manage the state of node data.
    * Handles actions to set node configuration, last task details, and full node data.
    * @param {State} state - The current state of the node data.
    * @param {Action} action - The action to perform on the state.
    * @returns {State} The new state after applying the action.
  */ 
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

/**
 * Custom hook to manage node data and operations.
 * 
 * @returns  {Object} An object containing node configuration, full node data, loading states, and handlers for node operations.
 * @property {NodeConfig | null} nodeConfig - The current node configuration.
 */
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

  /**
   * Fetches the current node status, including configuration and full node details.
   * Updates the state with the fetched data.
   */
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

  /**
   * Handles the registration of a new node with the given name.
   * Updates the node status after registration.
   * 
   * @param {string} name - The name of the node to register.
   */
  const handleRegisterNode = async (name: string) => {
    setIsRegistering(true);
    await registerNode(name);
    await fetchNodeStatus();
    setIsRegistering(false);
  };

  /**
   * Handles the start operation for the node.
   * Updates the node status after starting.
   */
  const handleStartNode = async () => {
    setIsStarting(true);
    await startNode();
    await fetchNodeStatus();
    setIsStarting(false);
  };

  /**
   * Handles the stop operation for the node.
   * Updates the node status after stopping.
   */
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
