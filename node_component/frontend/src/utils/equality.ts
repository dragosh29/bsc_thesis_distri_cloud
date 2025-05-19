export function shallowEqualExcept<T extends object>(
    a: T,
    b: T,
    exceptKeys: (keyof T)[]
  ): boolean {
    const keysA = Object.keys(a) as (keyof T)[];
    const keysB = Object.keys(b) as (keyof T)[];
  
    if (keysA.length !== keysB.length) return false;
  
    for (const key of keysA) {
      if (exceptKeys.includes(key)) continue;
      if (a[key] !== b[key]) return false;
    }
  
    return true;
  }
  
  export function shallowEqual<T extends object>(a: T, b: T): boolean {
    const keysA = Object.keys(a) as (keyof T)[];
    const keysB = Object.keys(b) as (keyof T)[];
  
    if (keysA.length !== keysB.length) return false;
  
    for (const key of keysA) {
      if (a[key] !== b[key]) return false;
    }
  
    return true;
  }
  