import React, { useMemo } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

/**
 * Renders text with inline LaTeX ($...$) and display LaTeX ($$...$$).
 * Splits text on LaTeX delimiters and renders math via KaTeX.
 */
const LatexRenderer = ({ text, className = '' }) => {
    const rendered = useMemo(() => {
        if (!text) return [];

        const parts = [];
        // Match both display ($$...$$) and inline ($...$) LaTeX
        // Use a regex that finds $$ first, then single $
        const regex = /\$\$([^$]+?)\$\$|\$([^$\n]+?)\$/g;

        let lastIndex = 0;
        let match;

        while ((match = regex.exec(text)) !== null) {
            // Add text before the match
            if (match.index > lastIndex) {
                parts.push({
                    type: 'text',
                    content: text.slice(lastIndex, match.index),
                });
            }

            const isDisplay = match[1] !== undefined;
            const latex = isDisplay ? match[1] : match[2];

            try {
                const html = katex.renderToString(latex.trim(), {
                    throwOnError: false,
                    displayMode: isDisplay,
                    trust: true,
                });
                parts.push({
                    type: isDisplay ? 'display-math' : 'inline-math',
                    html,
                });
            } catch {
                // If KaTeX fails, render as plain text
                parts.push({
                    type: 'text',
                    content: match[0],
                });
            }

            lastIndex = match.index + match[0].length;
        }

        // Add remaining text
        if (lastIndex < text.length) {
            parts.push({
                type: 'text',
                content: text.slice(lastIndex),
            });
        }

        return parts;
    }, [text]);

    if (!text) return null;

    return (
        <div className={className}>
            {rendered.map((part, i) => {
                if (part.type === 'text') {
                    // Split text by newlines and render with proper line breaks
                    const lines = part.content.split('\n');
                    return (
                        <React.Fragment key={i}>
                            {lines.map((line, j) => (
                                <React.Fragment key={j}>
                                    {j > 0 && <br />}
                                    {line}
                                </React.Fragment>
                            ))}
                        </React.Fragment>
                    );
                }

                if (part.type === 'display-math') {
                    return (
                        <div
                            key={i}
                            className="my-2 overflow-x-auto"
                            dangerouslySetInnerHTML={{ __html: part.html }}
                        />
                    );
                }

                // inline-math
                return (
                    <span
                        key={i}
                        dangerouslySetInnerHTML={{ __html: part.html }}
                    />
                );
            })}
        </div>
    );
};

export default LatexRenderer;
