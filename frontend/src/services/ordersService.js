import { mockOrders } from '../data/mockOrders.js';

export async function getOrders() {
  return structuredClone(mockOrders);
}