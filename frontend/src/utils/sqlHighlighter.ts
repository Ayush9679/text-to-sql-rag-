const SQL_KEYWORDS = new Set([
  'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'FULL',
  'ON', 'GROUP', 'BY', 'ORDER', 'HAVING', 'LIMIT', 'OFFSET', 'UNION', 'ALL',
  'AS', 'AND', 'OR', 'NOT', 'IN', 'IS', 'NULL', 'LIKE', 'ILIKE', 'BETWEEN',
  'EXISTS', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'ASC', 'DESC', 'WITH',
  'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'COALESCE', 'ROUND', 'DATE_TRUNC', 'EXTRACT',
  'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'TABLE', 'VIEW', 'INDEX'
]);

export interface SqlToken {
  type: 'keyword' | 'string' | 'number' | 'comment' | 'operator' | 'punctuation' | 'text';
  value: string;
}

export function tokenizeSql(sql: string): SqlToken[] {
  const tokens: SqlToken[] = [];
  let cursor = 0;

  while (cursor < sql.length) {
    const char = sql[cursor];

    // Single-line comment --
    if (char === '-' && sql[cursor + 1] === '-') {
      let end = sql.indexOf('\n', cursor);
      if (end === -1) end = sql.length;
      tokens.push({ type: 'comment', value: sql.substring(cursor, end) });
      cursor = end;
      continue;
    }

    // String literals '...'
    if (char === "'") {
      let end = cursor + 1;
      while (end < sql.length && sql[end] !== "'") {
        if (sql[end] === '\\') end++;
        end++;
      }
      tokens.push({ type: 'string', value: sql.substring(cursor, Math.min(end + 1, sql.length)) });
      cursor = Math.min(end + 1, sql.length);
      continue;
    }

    // Numbers
    if (/\d/.test(char)) {
      let end = cursor;
      while (end < sql.length && /[\d.]/.test(sql[end])) {
        end++;
      }
      tokens.push({ type: 'number', value: sql.substring(cursor, end) });
      cursor = end;
      continue;
    }

    // Operators & Punctuation
    if (/[(),;=<>+*\/%]/.test(char)) {
      tokens.push({ type: 'punctuation', value: char });
      cursor++;
      continue;
    }

    // Words / Identifiers / Keywords
    if (/[a-zA-Z_]/.test(char)) {
      let end = cursor;
      while (end < sql.length && /[a-zA-Z0-9_]/.test(sql[end])) {
        end++;
      }
      const word = sql.substring(cursor, end);
      if (SQL_KEYWORDS.has(word.toUpperCase())) {
        tokens.push({ type: 'keyword', value: word });
      } else {
        tokens.push({ type: 'text', value: word });
      }
      cursor = end;
      continue;
    }

    // Whitespace and others
    tokens.push({ type: 'text', value: char });
    cursor++;
  }

  return tokens;
}
