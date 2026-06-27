import { describe, expect, it } from 'vitest';
import { getAccessibleTabs } from '../access';

describe('getAccessibleTabs', () => {
  it('maps Gateway tabs to the current UI structure', () => {
    expect(
      getAccessibleTabs(
        'systemAdmin',
        ['chat', 'search', 'history', 'registry', 'documents', 'admin', 'monitor'],
        'prod',
      ),
    ).toEqual(['chat', 'documents', 'history', 'knowledgeProcessing', 'admin', 'qa']);
  });

  it('does not grant role-based tabs when prod contract is explicit', () => {
    expect(getAccessibleTabs('systemAdmin', ['chat', 'search', 'history'], 'prod')).toEqual([
      'chat',
      'documents',
      'history',
    ]);
  });

  it('keeps the complete role scenario in demo mode', () => {
    expect(getAccessibleTabs('knowledgeAdmin', undefined, 'demo')).toContain('knowledgeProcessing');
  });
});
