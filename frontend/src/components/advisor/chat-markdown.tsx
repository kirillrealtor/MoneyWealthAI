import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * Renders advisor responses as markdown — SAFELY.
 *
 * Security posture (the model's output is untrusted text):
 * - react-markdown does NOT render raw HTML (no rehype-raw) → no HTML injection.
 * - `img` is disallowed → the model can't embed remote images (tracking/SSRF).
 * - links open in a new tab with rel="noopener noreferrer nofollow"; react-markdown's
 *   default urlTransform already strips dangerous URL schemes (javascript:, data:).
 */
const components: Components = {
  p: ({ children }) => <p className="my-2 first:mt-0 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="my-2 ml-1 list-disc space-y-1 pl-4">{children}</ul>,
  ol: ({ children }) => <ol className="my-2 ml-1 list-decimal space-y-1 pl-4">{children}</ol>,
  li: ({ children }) => <li className="pl-0.5 marker:text-fg-subtle">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-fg">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  h1: ({ children }) => <h3 className="mb-1.5 mt-3 text-sm font-semibold text-fg">{children}</h3>,
  h2: ({ children }) => <h3 className="mb-1.5 mt-3 text-sm font-semibold text-fg">{children}</h3>,
  h3: ({ children }) => <h3 className="mb-1.5 mt-3 text-sm font-semibold text-fg">{children}</h3>,
  code: ({ children }) => (
    <code className="rounded bg-hover-strong px-1 py-0.5 font-mono text-[0.85em] text-fg">{children}</code>
  ),
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer nofollow"
      className="text-brand underline decoration-brand/40 underline-offset-2 hover:decoration-brand"
    >
      {children}
    </a>
  ),
  blockquote: ({ children }) => (
    <blockquote className="my-2 border-l-2 border-line pl-3 text-fg-muted">{children}</blockquote>
  ),
};

export function ChatMarkdown({ children }: { children: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={components}
      disallowedElements={["img"]}
      unwrapDisallowed
    >
      {children}
    </ReactMarkdown>
  );
}
