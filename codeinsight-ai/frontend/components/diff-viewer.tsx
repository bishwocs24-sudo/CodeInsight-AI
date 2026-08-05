"use client";

/**
 * Lightweight line-level diff viewer. Not a full Myers-diff algorithm -
 * it aligns by line index and flags lines that differ, which is enough
 * for "here's roughly what changed" without pulling in a diff library.
 */
export function DiffViewer({ original, refactored }: { original: string; refactored: string }) {
  const originalLines = original.split("\n");
  const refactoredLines = refactored.split("\n");
  const maxLines = Math.max(originalLines.length, refactoredLines.length);

  const rows = Array.from({ length: maxLines }, (_, i) => ({
    left: originalLines[i],
    right: refactoredLines[i],
    changed: originalLines[i] !== refactoredLines[i],
  }));

  return (
    <div className="grid grid-cols-2 gap-2 overflow-x-auto rounded-xl bg-muted p-3 text-xs font-mono">
      <div>
        <p className="mb-1 text-[10px] uppercase tracking-wide text-muted-foreground">Original</p>
        {rows.map((row, i) => (
          <div key={i} className={row.changed && row.left !== undefined ? "bg-red-500/10 text-red-300" : ""}>
            {row.left ?? ""}
          </div>
        ))}
      </div>
      <div>
        <p className="mb-1 text-[10px] uppercase tracking-wide text-muted-foreground">Refactored</p>
        {rows.map((row, i) => (
          <div key={i} className={row.changed && row.right !== undefined ? "bg-emerald-500/10 text-emerald-300" : ""}>
            {row.right ?? ""}
          </div>
        ))}
      </div>
    </div>
  );
}
