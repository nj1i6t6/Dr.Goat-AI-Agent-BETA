import { describe, it, expect } from 'vitest';
import { sanitizeHtml } from './sanitizeHtml';

describe('sanitizeHtml', () => {
  it('enforces rel attributes even when href is removed', () => {
    const malicious = '<p><a href="javascript:alert(1)">危險</a><a href="https://example.com">安全</a></p>';
    const sanitized = sanitizeHtml(malicious);

    expect(sanitized).toContain('<a rel="noopener noreferrer nofollow">危險</a>');
    expect(sanitized).toContain('href="https://example.com"');
    expect(sanitized).toContain('target="_blank"');
    expect(sanitized).toContain('rel="noopener noreferrer nofollow"');
  });
});
