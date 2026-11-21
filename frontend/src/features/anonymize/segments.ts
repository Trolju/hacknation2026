/**
 * Operacje na spanach po stronie klienta.
 *
 * Backend scala spany przy `apply`, ale podświetlenie w polu tekstowym wymaga
 * fragmentów rozłącznych już w przeglądarce — stąd te funkcje.
 */

import type { Span } from "@/lib/types";

export type Segment = { text: string; span?: Span };

/**
 * Dzieli tekst na fragmenty zwykłe i objęte spanem.
 *
 * Spany nachodzące na siebie lub wychodzące poza tekst są pomijane — po
 * edycji tekstu offsety mogą być nieaktualne i nie wolno nimi ciąć tekstu.
 */
export function buildSegments(text: string, spans: Span[]): Segment[] {
  const ordered = [...spans].sort((a, b) => a.start - b.start);
  const segments: Segment[] = [];
  let cursor = 0;
  for (const span of ordered) {
    if (span.start < cursor || span.end > text.length || span.start >= span.end) {
      continue;
    }
    if (span.start > cursor) {
      segments.push({ text: text.slice(cursor, span.start) });
    }
    segments.push({ text: text.slice(span.start, span.end), span });
    cursor = span.end;
  }
  if (cursor < text.length) {
    segments.push({ text: text.slice(cursor) });
  }
  return segments;
}

/** Dokłada span, usuwając wcześniejsze nakładające się zaznaczenia. */
export function withSpan(spans: Span[], next: Span): Span[] {
  const kept = spans.filter(
    (span) => span.end <= next.start || next.end <= span.start,
  );
  return [...kept, next].sort((a, b) => a.start - b.start);
}

/** Usuwa span wskazany przez pozycję i kategorię. */
export function withoutSpan(spans: Span[], target: Span): Span[] {
  return spans.filter(
    (span) =>
      !(
        span.start === target.start &&
        span.end === target.end &&
        span.category === target.category
      ),
  );
}
