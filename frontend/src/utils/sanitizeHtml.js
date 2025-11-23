import DOMPurify from 'dompurify';

const ALLOWED_TAGS = [
  'a',
  'p',
  'br',
  'strong',
  'em',
  'ul',
  'ol',
  'li',
  'code',
  'pre',
  'blockquote',
  'table',
  'thead',
  'tbody',
  'tr',
  'th',
  'td',
  'hr',
  'span',
  'div',
  'h1',
  'h2',
  'h3',
  'h4',
  'h5',
  'h6',
];

const ALLOWED_ATTR = ['href', 'title', 'rel', 'target', 'class'];
const LINK_REL_TOKENS = ['noopener', 'noreferrer', 'nofollow'];
const LINK_REL = LINK_REL_TOKENS.join(' ');

export function sanitizeHtml(html) {
  if (!html || typeof window === 'undefined') {
    return '';
  }

  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    if (node.tagName === 'A') {
      const existingRel = node.getAttribute('rel') || '';
      const relTokens = new Set(existingRel.split(/\s+/).filter(Boolean));
      LINK_REL_TOKENS.forEach((token) => relTokens.add(token));
      node.setAttribute(
        'rel',
        LINK_REL_TOKENS.filter((token) => relTokens.has(token)).join(' ')
      );

      if (node.hasAttribute('href')) {
        if (!node.hasAttribute('target')) {
          node.setAttribute('target', '_blank');
        }
      } else {
        node.removeAttribute('target');
      }
    }
  });

  try {
    return DOMPurify.sanitize(html, {
      ALLOWED_TAGS,
      ALLOWED_ATTR,
      ALLOW_DATA_ATTR: false,
      RETURN_TRUSTED_TYPE: false,
    });
  } finally {
    DOMPurify.removeHook('afterSanitizeAttributes');
  }
}
