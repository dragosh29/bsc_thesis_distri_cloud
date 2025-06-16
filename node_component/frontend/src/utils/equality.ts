/**
 * Shallowly compares two objects for equality, ignoring specified keys.
 * @param a The first object to compare.
 * @param b The second object to compare.
 * @param exceptKeys An array of keys to ignore during comparison.
 * @returns True if the objects are equal (excluding ignored keys), false otherwise.
*/
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

/**
 * Shallowly compares two objects for equality.
 * @param a The first object to compare.
 * @param b The second object to compare.
 * @returns True if the objects are equal, false otherwise.
 */
export function shallowEqual<T extends object>(a: T, b: T): boolean {
  const keysA = Object.keys(a) as (keyof T)[];
  const keysB = Object.keys(b) as (keyof T)[];

  if (keysA.length !== keysB.length) return false;

  for (const key of keysA) {
    if (a[key] !== b[key]) return false;
  }

  return true;
}
  