/**
 * Edytor treści projektu (TipTap).
 *
 * Kontrakt przechowuje Markdown, edytor pracuje na HTML — konwersja żyje
 * w `markdown.ts`. Komponent wystawia na zewnątrz dwie operacje przewijania:
 * do odnośnika `[^n]` i do dowolnego fragmentu tekstu (np. nagłówka sekcji
 * z twierdzeniem bez źródła).
 */

import Placeholder from "@tiptap/extension-placeholder";
import { EditorContent, useEditor, type Editor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import {
  Bold,
  Heading2,
  Heading3,
  List,
  ListOrdered,
  Redo2,
  Undo2,
} from "lucide-react";
import { forwardRef, useEffect, useImperativeHandle, useReducer, useRef } from "react";

import { Button } from "@/components/ui/button";
import { TEXT } from "@/features/drafting/i18n";
import { htmlToMarkdown, markdownToHtml } from "@/features/drafting/markdown";

export type DraftEditorHandle = {
  /** Ustawia kursor na odnośniku `[^n]`; `false`, gdy odnośnika nie ma w treści. */
  scrollToMarker: (ref: number) => boolean;
  /** Ustawia kursor na fragmencie tekstu; `false`, gdy fragmentu nie ma. */
  scrollToText: (text: string) => boolean;
};

type DraftEditorProps = {
  markdown: string;
  onChange: (markdown: string) => void;
  readOnly?: boolean;
};

function findTextPosition(editor: Editor, needle: string): number | null {
  const positions: number[] = [];
  editor.state.doc.descendants((node, pos) => {
    if (positions.length > 0) return false;
    if (!node.isText || !node.text) return true;
    const index = node.text.indexOf(needle);
    if (index >= 0) positions.push(pos + index);
    return positions.length === 0;
  });
  return positions.length > 0 ? positions[0] : null;
}

function selectRange(editor: Editor, position: number, length: number): void {
  editor
    .chain()
    .focus()
    .setTextSelection({ from: position, to: position + length })
    .scrollIntoView()
    .run();
}

export const DraftEditor = forwardRef<DraftEditorHandle, DraftEditorProps>(
  function DraftEditor({ markdown, onChange, readOnly = false }, ref) {
    const onChangeRef = useRef(onChange);
    onChangeRef.current = onChange;
    const applied = useRef(markdown);
    const [, rerender] = useReducer((value: number) => value + 1, 0);

    const editor = useEditor({
      extensions: [
        StarterKit.configure({ heading: { levels: [2, 3] } }),
        Placeholder.configure({ placeholder: TEXT.editorPlaceholder }),
      ],
      content: markdownToHtml(markdown),
      editable: !readOnly,
      editorProps: {
        attributes: {
          class: [
            "min-h-[420px] w-full px-4 py-3 text-sm leading-relaxed focus:outline-none",
            "[&_h2]:mt-4 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:tracking-tight",
            "[&_h3]:mt-3 [&_h3]:text-base [&_h3]:font-semibold",
            "[&_p]:my-2 [&_p]:leading-relaxed",
            "[&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-5",
            "[&_ol]:my-2 [&_ol]:list-decimal [&_ol]:pl-5",
            "[&_li]:my-0.5 [&_li_p]:my-0",
            "[&_strong]:font-semibold",
            "[&_.is-editor-empty:first-child::before]:float-left",
            "[&_.is-editor-empty:first-child::before]:h-0",
            "[&_.is-editor-empty:first-child::before]:text-muted-foreground",
            "[&_.is-editor-empty:first-child::before]:content-[attr(data-placeholder)]",
          ].join(" "),
          "aria-label": TEXT.editorTitle,
        },
      },
      onUpdate: ({ editor: instance }) => {
        const next = htmlToMarkdown(instance.getHTML());
        applied.current = next;
        onChangeRef.current(next);
      },
    });

    useEffect(() => {
      if (!editor) return;
      const update = () => rerender();
      editor.on("transaction", update);
      return () => {
        editor.off("transaction", update);
      };
    }, [editor]);

    useEffect(() => {
      if (!editor) return;
      if (markdown === applied.current) return;
      applied.current = markdown;
      editor.commands.setContent(markdownToHtml(markdown), false);
    }, [editor, markdown]);

    useImperativeHandle(
      ref,
      () => ({
        scrollToMarker: (refNumber: number) => {
          if (!editor) return false;
          const needle = `[^${refNumber}]`;
          const position = findTextPosition(editor, needle);
          if (position === null) return false;
          selectRange(editor, position, needle.length);
          return true;
        },
        scrollToText: (text: string) => {
          if (!editor) return false;
          const needle = text.trim();
          if (!needle) return false;
          const position = findTextPosition(editor, needle);
          if (position === null) return false;
          selectRange(editor, position, needle.length);
          return true;
        },
      }),
      [editor],
    );

    const toolbar = [
      {
        label: TEXT.toolbarHeading2,
        icon: Heading2,
        active: editor?.isActive("heading", { level: 2 }) ?? false,
        run: () => editor?.chain().focus().toggleHeading({ level: 2 }).run(),
      },
      {
        label: TEXT.toolbarHeading3,
        icon: Heading3,
        active: editor?.isActive("heading", { level: 3 }) ?? false,
        run: () => editor?.chain().focus().toggleHeading({ level: 3 }).run(),
      },
      {
        label: TEXT.toolbarBold,
        icon: Bold,
        active: editor?.isActive("bold") ?? false,
        run: () => editor?.chain().focus().toggleBold().run(),
      },
      {
        label: TEXT.toolbarBulletList,
        icon: List,
        active: editor?.isActive("bulletList") ?? false,
        run: () => editor?.chain().focus().toggleBulletList().run(),
      },
      {
        label: TEXT.toolbarOrderedList,
        icon: ListOrdered,
        active: editor?.isActive("orderedList") ?? false,
        run: () => editor?.chain().focus().toggleOrderedList().run(),
      },
    ];

    return (
      <div className="overflow-hidden rounded-lg border">
        <div className="flex flex-wrap items-center gap-1 border-b bg-muted/40 px-2 py-1.5">
          {toolbar.map((item) => (
            <Button
              key={item.label}
              type="button"
              size="sm"
              variant={item.active ? "secondary" : "ghost"}
              className="h-8 px-2"
              title={item.label}
              aria-label={item.label}
              aria-pressed={item.active}
              disabled={!editor || readOnly}
              onClick={item.run}
            >
              <item.icon className="h-4 w-4" />
            </Button>
          ))}
          <span className="mx-1 h-5 w-px bg-border" aria-hidden="true" />
          <Button
            type="button"
            size="sm"
            variant="ghost"
            className="h-8 px-2"
            title={TEXT.toolbarUndo}
            aria-label={TEXT.toolbarUndo}
            disabled={!editor || readOnly || !editor.can().undo()}
            onClick={() => editor?.chain().focus().undo().run()}
          >
            <Undo2 className="h-4 w-4" />
          </Button>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            className="h-8 px-2"
            title={TEXT.toolbarRedo}
            aria-label={TEXT.toolbarRedo}
            disabled={!editor || readOnly || !editor.can().redo()}
            onClick={() => editor?.chain().focus().redo().run()}
          >
            <Redo2 className="h-4 w-4" />
          </Button>
        </div>
        <EditorContent editor={editor} className="bg-background" />
      </div>
    );
  },
);
