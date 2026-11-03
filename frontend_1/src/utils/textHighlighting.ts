export interface HighlightSpan {
  start: number;
  end: number;
  type: 'contradiction' | 'tension' | 'risky' | 'safer' | 'neutral';
  label?: string;
  note?: string;
}

export interface TextSegment {
  text: string;
  isHighlighted: boolean;
  type?: 'contradiction' | 'tension' | 'risky' | 'safer' | 'neutral';
  label?: string;
  note?: string;
}

/**
 * Cleanly segment original text into highlighted and plain segments
 * strictly preserving all characters, casing, whitespace, and formatting.
 */
export function segmentTextBySpans(text: string, spans: HighlightSpan[]): TextSegment[] {
  if (!text) return [];
  if (!spans || spans.length === 0) {
    return [{ text, isHighlighted: false }];
  }

  // Filter and normalize valid spans within bounds
  const validSpans = spans
    .filter((s) => s.start >= 0 && s.end <= text.length && s.start < s.end)
    .sort((a, b) => a.start - b.start || b.end - a.end);

  if (validSpans.length === 0) {
    return [{ text, isHighlighted: false }];
  }

  // Deduplicate and merge overlapping or adjacent spans
  const mergedSpans: HighlightSpan[] = [];
  for (const span of validSpans) {
    if (mergedSpans.length === 0) {
      mergedSpans.push({ ...span });
      continue;
    }

    const prev = mergedSpans[mergedSpans.length - 1];
    if (span.start <= prev.end) {
      // Overlap detected: extend end boundary and combine notes if differing
      prev.end = Math.max(prev.end, span.end);
      if (span.label && !prev.label) prev.label = span.label;
    } else {
      mergedSpans.push({ ...span });
    }
  }

  const segments: TextSegment[] = [];
  let cursor = 0;

  for (const span of mergedSpans) {
    if (span.start > cursor) {
      segments.push({
        text: text.slice(cursor, span.start),
        isHighlighted: false,
      });
    }

    segments.push({
      text: text.slice(span.start, span.end),
      isHighlighted: true,
      type: span.type,
      label: span.label,
      note: span.note,
    });

    cursor = span.end;
  }

  if (cursor < text.length) {
    segments.push({
      text: text.slice(cursor),
      isHighlighted: false,
    });
  }

  return segments;
}

interface Token {
  raw: string;
  normalized: string;
  start: number;
  end: number;
  isWord: boolean;
}

function tokenize(text: string): Token[] {
  const tokens: Token[] = [];
  const regex = /([A-Za-z0-9_]+|[^\sA-Za-z0-9_]+|\s+)/g;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    const raw = match[0];
    const isWord = /^[A-Za-z0-9_]+$/.test(raw);
    tokens.push({
      raw,
      normalized: isWord ? raw.toLowerCase() : raw,
      start: match.index,
      end: match.index + raw.length,
      isWord,
    });
  }

  return tokens;
}

export interface ClauseDiffResult {
  hasDiff: boolean;
  originalSpans: HighlightSpan[];
  rewriteSpans: HighlightSpan[];
  overlapRatio: number;
}

/**
 * Computes deterministic word-level diff between original clause and suggested rewrite.
 * Words removed/changed from original are tagged as 'risky'.
 * Words added/changed in rewrite are tagged as 'safer'.
 */
export function computeClauseDiff(originalText: string, rewriteText: string): ClauseDiffResult {
  if (!originalText || !rewriteText) {
    return { hasDiff: false, originalSpans: [], rewriteSpans: [], overlapRatio: 0 };
  }

  const origTokens = tokenize(originalText);
  const rewrTokens = tokenize(rewriteText);

  const origWords = origTokens.filter((t) => t.isWord);
  const rewrWords = rewrTokens.filter((t) => t.isWord);

  if (origWords.length === 0 || rewrWords.length === 0) {
    return { hasDiff: false, originalSpans: [], rewriteSpans: [], overlapRatio: 0 };
  }

  const n = origWords.length;
  const m = rewrWords.length;

  // Build standard LCS matrix on word tokens
  const dp: number[][] = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));

  for (let i = 1; i <= n; i++) {
    for (let j = 1; j <= m; j++) {
      if (origWords[i - 1].normalized === rewrWords[j - 1].normalized) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  const lcsLength = dp[n][m];
  const overlapRatio = (2 * lcsLength) / (n + m);

  // Check if rewrite text is purely advisory guidance rather than a verbatim clause draft
  const isAdvisoryText = /^[-*•]?\s*(?:to\s+mitigate|consider|revising|it\s+is\s+recommended|the\s+clause\s+should\s+be|suggest\s+modifying|we\s+recommend)/i.test(rewriteText);

  // If text is advisory guidance or word overlap is low (< 40%), don't run token diffing.
  // This keeps advisory recommendations crystal-clear, clean, and professional without fragmented highlights.
  if (isAdvisoryText || overlapRatio < 0.40 || lcsLength < 5) {
    return { hasDiff: false, originalSpans: [], rewriteSpans: [], overlapRatio };
  }

  // Backtrack to find which words match
  const matchedOrigIndices = new Set<number>();
  const matchedRewrIndices = new Set<number>();

  let i = n;
  let j = m;

  while (i > 0 && j > 0) {
    if (origWords[i - 1].normalized === rewrWords[j - 1].normalized) {
      matchedOrigIndices.add(i - 1);
      matchedRewrIndices.add(j - 1);
      i--;
      j--;
    } else if (dp[i - 1][j] >= dp[i][j - 1]) {
      i--;
    } else {
      j--;
    }
  }

  // Words in original text not in LCS are risky / replaced phrasing
  const rawOrigSpans: HighlightSpan[] = [];
  for (let k = 0; k < origWords.length; k++) {
    if (!matchedOrigIndices.has(k)) {
      const w = origWords[k];
      rawOrigSpans.push({
        start: w.start,
        end: w.end,
        type: 'risky',
        label: 'Risky wording',
      });
    }
  }

  // Words in rewrite text not in LCS are safer alternative wording / additions
  const rawRewrSpans: HighlightSpan[] = [];
  for (let k = 0; k < rewrWords.length; k++) {
    if (!matchedRewrIndices.has(k)) {
      const w = rewrWords[k];
      rawRewrSpans.push({
        start: w.start,
        end: w.end,
        type: 'safer',
        label: 'Safer rewrite change',
      });
    }
  }

  const originalSpans = mergeAdjacentSpans(rawOrigSpans, originalText);
  const rewriteSpans = mergeAdjacentSpans(rawRewrSpans, rewriteText);

  return {
    hasDiff: true,
    originalSpans,
    rewriteSpans,
    overlapRatio,
  };
}

/**
 * Merge spans that are separated only by small whitespace, punctuation, or short connector words
 * to create clean, continuous, legible highlight blocks instead of fragmented words.
 */
function mergeAdjacentSpans(spans: HighlightSpan[], fullText: string): HighlightSpan[] {
  if (spans.length <= 1) return spans;

  const merged: HighlightSpan[] = [];
  let current = { ...spans[0] };

  for (let i = 1; i < spans.length; i++) {
    const next = spans[i];
    const gap = fullText.slice(current.end, next.start);

    // If gap between words is short (whitespace, punctuation, or 1 connector word), merge into one smooth highlight
    if (gap.length <= 8 || /^\s*(?:the|of|to|and|in|a|an|for|with|by|on)?\s*$/i.test(gap)) {
      current.end = next.end;
    } else {
      merged.push(current);
      current = { ...next };
    }
  }
  merged.push(current);

  return merged;
}

export interface ExtractedRewrite {
  clauseText: string;
  rationale: string;
  hasQuotedClause: boolean;
  isAdvisory: boolean;
}

/**
 * Inspects LLM rewrite suggestion to separate verbatim clause drafts from introductory rationale.
 */
export function extractRewriteDetails(rawRewrite: string): ExtractedRewrite {
  if (!rawRewrite) {
    return { clauseText: '', rationale: '', hasQuotedClause: false, isAdvisory: false };
  }

  const clean = rawRewrite.trim();

  // Check for standard quotation marks enclosing a clause
  const quoteMatch = clean.match(/(?:["“]([^"”]{20,})["”]|(?:such as:?\s*\n*["“]?([^"”\n]{25,})))$/i);
  if (quoteMatch) {
    const quoted = (quoteMatch[1] || quoteMatch[2] || '').trim();
    const rationale = clean.replace(quoted, '').replace(/["“”]/g, '').trim();
    if (quoted.length > 20) {
      return {
        clauseText: quoted,
        rationale: rationale || 'Consider adopting the revised wording below to limit liability and specify unambiguous performance obligations.',
        hasQuotedClause: true,
        isAdvisory: false,
      };
    }
  }

  // If text starts with an introductory advisory sentence followed by a colon or newline
  const introSplit = clean.split(/:\s*\n+|\n\n+/);
  if (introSplit.length > 1 && introSplit[1].trim().length > 20) {
    return {
      clauseText: introSplit.slice(1).join('\n\n').replace(/^["“]|["”]$/g, '').trim(),
      rationale: introSplit[0].trim(),
      hasQuotedClause: true,
      isAdvisory: false,
    };
  }

  const isAdvisory = /^[-*•]?\s*(?:to\s+mitigate|consider|revising|it\s+is\s+recommended|the\s+clause\s+should\s+be|suggest\s+modifying|we\s+recommend)/i.test(clean);

  return {
    clauseText: clean.replace(/^[-*•]\s*/, '').replace(/^["“]|["”]$/g, ''),
    rationale: 'Review the proposed drafting revision to replace one-sided stipulations with legally balanced commitments.',
    hasQuotedClause: false,
    isAdvisory,
  };
}
