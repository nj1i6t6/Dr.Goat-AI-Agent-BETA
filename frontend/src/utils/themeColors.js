export function readCssVar(name, fallback = '') {
  if (typeof window === 'undefined') return fallback;
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

export function withAlpha(color, alpha) {
  if (!color) return '';
  if (color.startsWith('#')) {
    const hex = color.slice(1);
    const normalized = hex.length === 3 ? hex.split('').map((char) => char + char).join('') : hex;
    const bigint = parseInt(normalized, 16);
    const r = (bigint >> 16) & 255;
    const g = (bigint >> 8) & 255;
    const b = bigint & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  const rgbMatch = color.match(/\d+(?:\.\d+)?/g);
  if (!rgbMatch || rgbMatch.length < 3) {
    return color;
  }

  const [r, g, b] = rgbMatch;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
