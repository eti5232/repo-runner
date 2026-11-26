/**
 * הופכת שגיאה מהשרת לטקסט קריא. השרת שומר אותה כ-JSON ({error, message}) או כמו
 * ש-Python מדפיס אותה (SourceError('...')), ולמשתמשת רוצים להציג רק את ההסבר.
 */
export function errorText(raw: string): string {
  try {
    const parsed = JSON.parse(raw) as { message?: string };
    if (parsed.message) return parsed.message;
  } catch {
    // לא JSON: ממשיכים לצורה של Python
  }
  const python = raw.match(/^\w*(?:Error|Exception)\((['"])([\s\S]*)\1\)$/);
  return python ? python[2].replace(/\\\\/g, "\\").replace(/\\n/g, "\n") : raw;
}
