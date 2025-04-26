import { useEffect, useState } from 'react';
import { getHighlighter } from 'shiki';

export default function CodeHighlighter({ code, language }) {
  const [highlightedCode, setHighlightedCode] = useState('');

  useEffect(() => {
    async function highlight() {
      const highlighter = await getHighlighter({
        theme: 'github-dark',
        langs: [language],
      });
      const html = highlighter.codeToHtml(code, { lang: language });
      setHighlightedCode(html);
    }
    highlight();
  }, [code, language]);

  return (
    <div dangerouslySetInnerHTML={{ __html: highlightedCode }} />
  );
}