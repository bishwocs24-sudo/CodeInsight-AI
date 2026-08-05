"use client";

import Editor from "@monaco-editor/react";
import type { Language } from "@/lib/types";

interface CodeEditorProps {
  value: string;
  language: Language;
  onChange: (value: string) => void;
}

// Monaco's language ids don't always match our own; map the few that differ.
const MONACO_LANGUAGE: Partial<Record<Language, string>> = {
  cpp: "cpp",
  csharp: "csharp",
};

export function CodeEditor({ value, language, onChange }: CodeEditorProps) {
  return (
    <div className="overflow-hidden rounded-2xl border border-border">
      <Editor
        height="480px"
        theme="vs-dark"
        language={MONACO_LANGUAGE[language] ?? language}
        value={value}
        onChange={(val) => onChange(val ?? "")}
        options={{
          fontSize: 14,
          minimap: { enabled: false },
          padding: { top: 16 },
          scrollBeyondLastLine: false,
          fontFamily:
            "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        }}
      />
    </div>
  );
}
