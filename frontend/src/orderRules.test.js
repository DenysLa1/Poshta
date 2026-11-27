import test from 'node:test';
import assert from 'node:assert/strict';
import { canTransition } from './orderRules.js';

test('FSM permits only the configured next transitions', () => {
  const transitions = [
    ['NewOrder', 'Registered', true],
    ['NewOrder', 'Cancelled', true],
    ['Registered', 'Granted', true],
    ['Registered', 'Cancelled', true],
    ['Granted', 'Shipped', true],
    ['Granted', 'Cancelled', true],
    ['Shipped', 'Invoiced', true],
    ['Registered', 'Shipped', false],
    ['NewOrder', 'Granted', false],
    ['Shipped', 'Cancelled', false],
    ['Invoiced', 'Cancelled', false],
    ['Cancelled', 'Registered', false],
    ['Unknown', 'Registered', false],
  ];

  for (const [current, next, expected] of transitions) {
    assert.equal(canTransition(current, next), expected, `${current} -> ${next}`);
  }
});
