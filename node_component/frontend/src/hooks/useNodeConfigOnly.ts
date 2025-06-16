import { useMemo, useRef } from 'react';
import { useNodeData } from './useNodeData';
import { NodeConfig } from '../types/api';
import { shallowEqual } from '../utils/equality';

/*
  * Custom hook to extract only the node configuration data without resource usage.
  * This is useful for components that only need the configuration details.
  * 
  *  Returns an object containing:
  *  - `nodeConfig`: The cleaned NodeConfig object without resource usage.
  *  - `isLoading`: A boolean indicating if the data is still being loaded.
  *  @returns {Object} An object with `nodeConfig` and `isLoading` properties.
*/
export function useNodeConfigOnly(): { nodeConfig: NodeConfig | null; isLoading: boolean } {
  const { nodeConfig, isLoading } = useNodeData();
  const lastStable = useRef<NodeConfig | null>(null);

  const cleaned = useMemo(() => {
    if (!nodeConfig) return null;
    const { resource_usage, ...rest } = nodeConfig;
    return rest as NodeConfig;
  }, [nodeConfig]);

  const stableNodeConfig = useMemo(() => {
    if (!cleaned) {
      return null;
    }
  
    if (!lastStable.current || !shallowEqual(lastStable.current, cleaned)) {
      lastStable.current = cleaned;
    }
  
    return lastStable.current;
  }, [cleaned]);
  

  return { nodeConfig: stableNodeConfig, isLoading };
}
