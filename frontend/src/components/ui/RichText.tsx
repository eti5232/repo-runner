/** מציג טקסט שהמודל כתב, ומעצב קטעים בין גרשיים הפוכים (`כך`) כקוד. */
export function RichText({ text }: { text: string }) {
  const parts = text.split(/`([^`]+)`/g);
  return (
    <>
      {parts.map((part, index) =>
        index % 2 === 1 ? (
          <code key={index} className="mx-0.5 rounded-md bg-inset px-1.5 py-0.5 text-[0.85em] text-ink-2">
            {part}
          </code>
        ) : (
          <span key={index}>{part}</span>
        ),
      )}
    </>
  );
}
