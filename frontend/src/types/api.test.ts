import { describe, it, expect } from 'vitest';

describe('API types', () => {
  it('should have correct type structure', () => {
    // Type-only test - if this compiles, types are valid
    const event: import('../types/api').OCSFEventCreate = {
      class_uid: 4001,
      activity_id: 1,
      category_uid: 4,
      category_name: 'Network Activity',
      class_name: 'Network Connection',
      time: new Date().toISOString(),
      severity_id: 1,
      severity: 'Informational',
      status_id: 1,
      status: 'Success',
    };
    expect(event.class_uid).toBe(4001);
  });
});