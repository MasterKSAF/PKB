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

  it('shows QA for knowledge admins who can manage the registry', () => {
    expect(
      getAccessibleTabs(
        'knowledgeAdmin',
        ['chat', 'search', 'history', 'registry', 'documents'],
        'prod',
        { can_manage_registry: true },
      ),
    ).toEqual(['chat', 'documents', 'history', 'knowledgeProcessing', 'qa']);
  });

  it('keeps History visible for system admins when Gateway omits history', () => {
    expect(
      getAccessibleTabs(
        'systemAdmin',
        ['chat', 'search', 'registry', 'documents', 'admin', 'monitor'],
        'prod',
        { can_manage_users: true },
      ),
    ).toEqual(['chat', 'documents', 'knowledgeProcessing', 'admin', 'qa', 'history']);
  });

  it('does not grant any tabs in prod when backend omits available_tabs', () => {
    expect(getAccessibleTabs('systemAdmin', undefined, 'prod')).toEqual([]);
  });

  it('keeps the complete role scenario in demo mode', () => {
    expect(getAccessibleTabs('knowledgeAdmin', undefined, 'demo')).toContain('knowledgeProcessing');
  });
});
