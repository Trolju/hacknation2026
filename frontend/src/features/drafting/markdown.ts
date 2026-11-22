/**
 * Konwersja między Markdownem projektu a HTML edytora TipTap.
 *
 * Kontrakt przechowuje treść jako Markdown z odnośnikami `[^n]` (tak samo
 * czyta ją eksport DOCX/PDF), a edytor pracuje na HTML. Obsługujemy dokładnie
 * ten podzbiór, który powstaje w generatorze: nagłówki, akapity, listy,
 * pogrubienie i kursywę. Odnośniki `[^n]` zostają zwykłym tekstem — urzędnik
 * widzi je w treści i może je przenieść albo usunąć.
 */

export type DraftSection = {
  heading: string | null;
  text: string;
};

const HEADING = /^(#{1,6})\s+(.*)$/;
const BULLET = /^[-*+]\s+(.*)$/;
const NUMBERED = /^\d+[.)]\s+(.*)$/;
const VOID_TAGS = new Set(["br", "hr", "img"]);

function escapeHtml(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function decodeEntities(text: string): string {
  return text
    .replace(/&nbsp;/g, " ")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&");
}

function inlineToHtml(text: string): string {
  return escapeHtml(text)
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*\n]+)\*/g, "<em>$1</em>");
}

/** Markdown projektu → HTML dla edytora. */
export function markdownToHtml(markdown: string): string {
  const out: string[] = [];
  let paragraph: string[] = [];
  let list: "ul" | "ol" | null = null;

  const flushParagraph = () => {
    if (paragraph.length > 0) {
      out.push(`<p>${inlineToHtml(paragraph.join(" "))}</p>`);
      paragraph = [];
    }
  };
  const closeList = () => {
    if (list) {
      out.push(`</${list}>`);
      list = null;
    }
  };

  for (const rawLine of markdown.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) {
      flushParagraph();
      closeList();
      continue;
    }

    const heading = HEADING.exec(line);
    if (heading) {
      flushParagraph();
      closeList();
      const level = Math.min(heading[1].length, 3);
      out.push(`<h${level}>${inlineToHtml(heading[2].trim())}</h${level}>`);
      continue;
    }

    const bullet = BULLET.exec(line);
    if (bullet) {
      flushParagraph();
      if (list !== "ul") {
        closeList();
        out.push("<ul>");
        list = "ul";
      }
      out.push(`<li><p>${inlineToHtml(bullet[1].trim())}</p></li>`);
      continue;
    }

    const numbered = NUMBERED.exec(line);
    if (numbered) {
      flushParagraph();
      if (list !== "ol") {
        closeList();
        out.push("<ol>");
        list = "ol";
      }
      out.push(`<li><p>${inlineToHtml(numbered[1].trim())}</p></li>`);
      continue;
    }

    closeList();
    paragraph.push(line);
  }

  flushParagraph();
  closeList();
  return out.join("");
}

type HtmlNode = { tag: string; children: HtmlChild[] };
type HtmlChild = HtmlNode | string;

function parseHtml(html: string): HtmlNode {
  const root: HtmlNode = { tag: "root", children: [] };
  const stack: HtmlNode[] = [root];
  const pattern = /<(\/?)([a-zA-Z0-9]+)([^>]*)>/g;
  let cursor = 0;
  let match: RegExpExecArray | null = pattern.exec(html);

  while (match !== null) {
    const text = html.slice(cursor, match.index);
    if (text) stack[stack.length - 1].children.push(decodeEntities(text));
    cursor = match.index + match[0].length;

    const tag = match[2].toLowerCase();
    if (match[1] === "/") {
      for (let index = stack.length - 1; index > 0; index -= 1) {
        if (stack[index].tag === tag) {
          stack.length = index;
          break;
        }
      }
    } else {
      const node: HtmlNode = { tag, children: [] };
      stack[stack.length - 1].children.push(node);
      if (!VOID_TAGS.has(tag) && !match[3].trimEnd().endsWith("/")) {
        stack.push(node);
      }
    }
    match = pattern.exec(html);
  }

  const tail = html.slice(cursor);
  if (tail) stack[stack.length - 1].children.push(decodeEntities(tail));
  return root;
}

function inlineToMarkdown(node: HtmlNode): string {
  return node.children
    .map((child) => {
      if (typeof child === "string") return child;
      switch (child.tag) {
        case "strong":
        case "b":
          return `**${inlineToMarkdown(child)}**`;
        case "em":
        case "i":
          return `*${inlineToMarkdown(child)}*`;
        case "br":
          return "\n";
        case "code":
          return `\`${inlineToMarkdown(child)}\``;
        default:
          return inlineToMarkdown(child);
      }
    })
    .join("");
}

function blocksToMarkdown(node: HtmlNode): string[] {
  const lines: string[] = [];
  for (const child of node.children) {
    if (typeof child === "string") {
      const text = child.trim();
      if (text) lines.push(text);
      continue;
    }

    const heading = /^h([1-6])$/.exec(child.tag);
    if (heading) {
      lines.push(`${"#".repeat(Number(heading[1]))} ${inlineToMarkdown(child).trim()}`, "");
      continue;
    }
    if (child.tag === "p") {
      lines.push(inlineToMarkdown(child).trim(), "");
      continue;
    }
    if (child.tag === "ul" || child.tag === "ol") {
      const items = child.children.filter(
        (item): item is HtmlNode => typeof item !== "string" && item.tag === "li",
      );
      items.forEach((item, index) => {
        const marker = child.tag === "ol" ? `${index + 1}.` : "-";
        lines.push(`${marker} ${inlineToMarkdown(item).trim()}`);
      });
      lines.push("");
      continue;
    }
    if (child.tag === "blockquote") {
      lines.push(
        ...blocksToMarkdown(child).map((line) => (line ? `> ${line}` : line)),
      );
      continue;
    }
    lines.push(...blocksToMarkdown(child));
  }
  return lines;
}

/** HTML edytora → Markdown projektu. */
export function htmlToMarkdown(html: string): string {
  const lines = blocksToMarkdown(parseHtml(html));
  return lines
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

/** Dzieli treść na sekcje wyznaczone nagłówkami. */
export function splitSections(markdown: string): DraftSection[] {
  const sections: DraftSection[] = [];
  let heading: string | null = null;
  let lines: string[] = [];

  const flush = () => {
    sections.push({
      heading,
      text: lines.join(" ").replace(/\s+/g, " ").trim(),
    });
    lines = [];
  };

  for (const rawLine of markdown.split(/\r?\n/)) {
    const match = HEADING.exec(rawLine.trim());
    if (match) {
      flush();
      heading = match[2].trim();
      continue;
    }
    lines.push(rawLine);
  }
  flush();
  return sections;
}

/**
 * Nagłówek sekcji, w której pada twierdzenie bez źródła.
 *
 * Zdania w `unsupported` pochodzą z treści projektu, więc szukamy ich po
 * pierwszym fragmencie — model mógł zawinąć wiersz w środku zdania.
 */
export function sectionForClaim(markdown: string, claim: string): string | null {
  const needle = claim.replace(/\s+/g, " ").trim().slice(0, 40);
  if (!needle) return null;
  for (const section of splitSections(markdown)) {
    if (section.heading && section.text.includes(needle)) return section.heading;
  }
  return null;
}

/** Numery odnośników użytych w treści, w kolejności wystąpienia. */
export function citationRefs(markdown: string): number[] {
  const refs: number[] = [];
  for (const match of markdown.matchAll(/\[\^(\d+)\]/g)) {
    const ref = Number(match[1]);
    if (!refs.includes(ref)) refs.push(ref);
  }
  return refs;
}

/**
 * Zakres odnośników obejmujący numer — `[^2]–[^13]` zawiera także 5.
 *
 * Generator zwęża przebiegi trzech i więcej odnośników do zakresu, więc
 * kliknięcie cytowania ze środka zakresu nie znajdzie własnego `[^n]`.
 */
export function markerRangeFor(markdown: string, ref: number): string | null {
  for (const match of markdown.matchAll(/\[\^(\d+)\]–\[\^(\d+)\]/g)) {
    const start = Number(match[1]);
    const end = Number(match[2]);
    if (ref >= start && ref <= end) return match[0];
  }
  return null;
}
