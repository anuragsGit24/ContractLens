import type { Clause, ClauseExplanation } from '../types/contract';
import type { HighlightSpan } from './textHighlighting';

export interface ContradictionAnalysis {
  clauseAIndex: number;
  clauseBIndex: number;
  score: number;
  topic: string;
  explanation: string;
  detailedReason: string;
  remedySuggestion: string;
  hasExactSpans: boolean;
  spansA: HighlightSpan[];
  spansB: HighlightSpan[];
  conflictType: 'TIMEFRAME' | 'MUTUAL_EXCLUSIVE' | 'POLARITY' | 'PREMISE_DIVERGENCE' | 'GENERAL_TENSION';
}

// Regex definitions for legal analysis
const TIMEFRAME_REGEX = /\b(?:within\s+)?(?:net\s+)?(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|fifteen|twenty|thirty|sixty|ninety|120|180|360|365)\s*(?:calendar\s+|business\s+)?(?:days?|months?|years?|weeks?|hours?)\b/gi;
const NOTICE_REGEX = /\b(?:\d+|one|two|three|five|ten|fifteen|twenty|thirty|sixty|ninety)\s*days?'?\s+(?:prior\s+|written\s+)?notice\b/gi;
const PERCENT_OR_AMOUNT_REGEX = /\b(?:(?:[\$€₹]|USD|INR|EUR|Rs\.?)\s*[\d,]+(?:\.\d+)?(?:\s*(?:million|crore|lakh|billion))?|\d+(?:\.\d+)?%)\b/gi;

const POSITIVE_OBLIGATION = /\b(shall\s+have\s+the\s+right|shall|must|is\s+required\s+to|agrees\s+to|is\s+obligated\s+to|will\s+provide|guarantees|ensures|warrants\s+that|warrants|is\s+entitled\s+to\s+receive|shall\s+be\s+permitted\s+to|shall\s+be\s+considered\s+valid|valid\s+and\s+legally\s+binding)\b/gi;
const NEGATIVE_PROHIBITION = /\b(shall\s+not\s+affect|shall\s+not\s+be\s+construed|shall\s+not|must\s+not|not\s+liable|without\s+liability|no\s+liability|not\s+responsible|is\s+not\s+responsible|will\s+not|is\s+not\s+required\s+to|shall\s+in\s+no\s+event|excluded|waived|waiver|disclaims|does\s+not|is\s+to\s+that\s+extent\s+void|shall\s+not\s+be\s+enforced|commits\s+the\s+offence|supersedes\s+all\s+prior)\b/gi;

const SUBJECT_KEYWORDS: Array<{ name: string; pattern: RegExp }> = [
  { name: 'payment & invoicing', pattern: /\b(payment|pay|invoice|fee|billing|remittance)\b/i },
  { name: 'notice & communication', pattern: /\b(notice|notify|notified|written notice)\b/i },
  { name: 'termination & remedies', pattern: /\b(terminat\w*|cure\s+period|cancel\w*|expire|without\s+liability)\b/i },
  { name: 'liability & damages', pattern: /\b(liab\w*|damages|indemnif\w*|losses|expenses|charges)\b/i },
  { name: 'entire agreement & integration', pattern: /\b(complete\s+and\s+exclusive|supersede\w*|entire\s+agreement|prior\s+representations)\b/i },
  { name: 'warranties & consideration', pattern: /\b(warrant\w*|rebate\w*|kickback\w*|unlawful\s+consideration)\b/i },
  { name: 'restraint of trade', pattern: /\b(restrain\w*|trade|profession|business|non-compete|compete)\b/i },
  { name: 'penalties & compensation', pattern: /\b(penalty|penalties|compensation|exorbitant|liquidated)\b/i },
  { name: 'intellectual property', pattern: /\b(ip|intellectual property|copyright|patent|trademark)\b/i },
  { name: 'confidentiality', pattern: /\b(confidential\w*|non-disclosure|secret)\b/i },
  { name: 'fraud & inducement', pattern: /\b(fraud\w*|dishonest\w*|deceiv\w*|cheating|prosecution)\b/i },
  { name: 'governing law & jurisdiction', pattern: /\b(jurisdiction|governing law|dispute resolution|arbitration|courts)\b/i },
  { name: 'severability & waiver', pattern: /\b(invalidity|severab\w*|waiver|construed\s+as\s+a\s+waiver)\b/i },
];

interface AntonymRule {
  a: RegExp;
  b: RegExp;
  topic: string;
  descA: string;
  descB: string;
}

const ANTONYM_RULES: AntonymRule[] = [
  {
    a: /\b(?:complete\s+and\s+exclusive\s+statement|supersedes\s+all\s+prior\s+(?:representations|understandings|communications)|entire\s+agreement)\b/i,
    b: /\b(?:warrants?\s+that|remedy\s+for\s+breach|terminate(?:\s+the\s+agreement)?\s+without\s+liability|unlawful\s+consideration|rebates?)\b/i,
    topic: 'entire agreement integration vs warranty remedies',
    descA: 'complete integration superseding prior representations',
    descB: 'pre-contractual warranty and unilateral termination remedy',
  },
  {
    a: /\b(?:shall\s+not\s+affect\s+the\s+validity|shall\s+not\s+be\s+construed\s+as\s+a\s+waiver)\b/i,
    b: /\b(?:terminate(?:\s+the\s+agreement)?\s+without\s+liability|sole\s+discretion\s+to\s+terminate)\b/i,
    topic: 'severability & non-waiver vs termination without liability',
    descA: 'severability and non-waiver restriction',
    descB: 'discretionary termination without liability',
  },
  {
    a: /\bexclusive\b/i,
    b: /\bnon-exclusive\b/i,
    topic: 'exclusivity rights',
    descA: 'exclusive rights',
    descB: 'non-exclusive rights',
  },
  {
    a: /\b(?:valid(?:\s+and\s+legally\s+binding)?)\b/i,
    b: /\b(?:void|unenforceable)\b/i,
    topic: 'legal enforceability',
    descA: 'valid and binding',
    descB: 'void and unenforceable',
  },
  {
    a: /\bunlimited\s+liability\b/i,
    b: /\b(?:capped|limited\s+to|shall\s+not\s+exceed)\b/i,
    topic: 'liability exposure',
    descA: 'unlimited liability',
    descB: 'capped/limited liability',
  },
  {
    a: /\bsole\s+discretion\b/i,
    b: /\b(?:mutual\s+consent|mutual\s+agreement|prior\s+written\s+consent)\b/i,
    topic: 'approval standard',
    descA: 'unilateral sole discretion',
    descB: 'mutual consent requirement',
  },
  {
    a: /\bperpetual\b/i,
    b: /\b(?:terminable\s+at\s+will|for\s+a\s+period\s+of|temporary)\b/i,
    topic: 'term & duration',
    descA: 'perpetual term',
    descB: 'limited duration/terminable term',
  },
  {
    a: /\birrevocable\b/i,
    b: /\brevocable\b/i,
    topic: 'revocability',
    descA: 'irrevocable license/grant',
    descB: 'revocable terms',
  },
  {
    a: /\bwithout\s+notice\b/i,
    b: /\bupon\s+(?:written\s+)?notice\b/i,
    topic: 'notice requirements',
    descA: 'action without notice',
    descB: 'prior notice mandate',
  },
  {
    a: /\bwith\s+cause\b/i,
    b: /\bwithout\s+cause\b/i,
    topic: 'termination justification',
    descA: 'termination with cause only',
    descB: 'termination without cause',
  },
  {
    a: /\bexorbitant\s+compensation\b/i,
    b: /\bshall\s+not\s+exceed\s+the\s+actual\s+damage\b/i,
    topic: 'damages vs penalties',
    descA: 'entitlement to exorbitant compensation',
    descB: 'restriction to actual damage caused',
  },
];

function splitSentences(text: string): Array<{ text: string; start: number; end: number }> {
  const result: Array<{ text: string; start: number; end: number }> = [];
  const regex = /[^.!?\n]+[.!?\n]+/g;
  let match: RegExpExecArray | null;
  let lastIndex = 0;

  while ((match = regex.exec(text)) !== null) {
    result.push({
      text: match[0],
      start: match.index,
      end: match.index + match[0].length,
    });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    const trailing = text.slice(lastIndex).trim();
    if (trailing.length > 0) {
      result.push({
        text: text.slice(lastIndex),
        start: lastIndex,
        end: text.length,
      });
    }
  }

  return result;
}

/**
 * Extracts a complete, readable clause segment (e.g. up to semicolon, period, or comma boundary)
 * around an operative keyword match so the highlighted passage is legible and meaningful.
 */
function extractOperativePhrase(
  fullText: string,
  matchStart: number,
  matchEnd: number
): { start: number; end: number; text: string } {
  const prevText = fullText.slice(0, matchStart);
  const nextText = fullText.slice(matchEnd);

  // Find nearest sentence, semicolon, or line boundary
  const lastSemi = prevText.lastIndexOf(';');
  const lastDot = prevText.lastIndexOf('. ');
  const lastNewline = prevText.lastIndexOf('\n');

  let clauseStart = Math.max(
    lastSemi !== -1 ? lastSemi + 1 : 0,
    lastDot !== -1 ? lastDot + 2 : 0,
    lastNewline !== -1 ? lastNewline + 1 : 0
  );

  // If start is still far from match (> 90 chars), check for comma clause boundary
  if (matchStart - clauseStart > 90) {
    const lastComma = prevText.lastIndexOf(', ');
    if (lastComma !== -1 && matchStart - lastComma < 90) {
      clauseStart = lastComma + 2;
    }
  }

  // Find next boundary
  const nextSemi = nextText.indexOf(';');
  const nextDot = nextText.indexOf('. ');
  const nextNewline = nextText.indexOf('\n');

  let clauseEndRelative = nextText.length;
  if (nextSemi !== -1 && nextSemi < clauseEndRelative) clauseEndRelative = nextSemi;
  if (nextDot !== -1 && nextDot < clauseEndRelative) clauseEndRelative = nextDot;
  if (nextNewline !== -1 && nextNewline < clauseEndRelative) clauseEndRelative = nextNewline;

  let clauseEnd = matchEnd + clauseEndRelative;

  // Trim whitespace boundaries from the span
  const rawSpan = fullText.slice(clauseStart, clauseEnd);
  const leadingSpaces = rawSpan.match(/^\s*/)?.[0].length || 0;
  const trailingSpaces = rawSpan.match(/\s*$/)?.[0].length || 0;

  const finalStart = clauseStart + leadingSpaces;
  const finalEnd = Math.max(finalStart + (matchEnd - matchStart), clauseEnd - trailingSpaces);

  return {
    start: finalStart,
    end: finalEnd,
    text: fullText.slice(finalStart, finalEnd),
  };
}

function findSharedSubject(textA: string, textB: string): string | null {
  for (const s of SUBJECT_KEYWORDS) {
    if (s.pattern.test(textA) && s.pattern.test(textB)) {
      return s.name;
    }
  }
  return null;
}

export function analyzeContradiction(
  clauseA: Clause,
  clauseB: Clause,
  score: number,
  explanations?: ClauseExplanation[]
): ContradictionAnalysis {
  const textA = clauseA?.text || '';
  const textB = clauseB?.text || '';
  const sharedSubject = findSharedSubject(textA, textB);

  // Check if LLM explanation for either clause contains contextual clues
  const relevantExplanation = explanations?.find(
    (e) => e.clause_index === clauseA.index || e.clause_index === clauseB.index
  );

  // -------------------------------------------------------------
  // Strategy 1: Check for Timeframe, Deadline, or Metric Conflicts
  // -------------------------------------------------------------
  const timeMatchesA = [...textA.matchAll(TIMEFRAME_REGEX), ...textA.matchAll(NOTICE_REGEX), ...textA.matchAll(PERCENT_OR_AMOUNT_REGEX)];
  const timeMatchesB = [...textB.matchAll(TIMEFRAME_REGEX), ...textB.matchAll(NOTICE_REGEX), ...textB.matchAll(PERCENT_OR_AMOUNT_REGEX)];

  if (timeMatchesA.length > 0 && timeMatchesB.length > 0) {
    // Find the pair of timeframes that differ
    for (const mA of timeMatchesA) {
      for (const mB of timeMatchesB) {
        const valA = mA[0].trim().toLowerCase();
        const valB = mB[0].trim().toLowerCase();

        if (valA !== valB) {
          const startA = mA.index!;
          const endA = startA + mA[0].length;
          const startB = mB.index!;
          const endB = startB + mB[0].length;

          const topic = sharedSubject || 'deadline & performance timeline';
          return {
            clauseAIndex: clauseA.index,
            clauseBIndex: clauseB.index,
            score,
            topic,
            conflictType: 'TIMEFRAME',
            hasExactSpans: true,
            spansA: [
              {
                start: startA,
                end: endA,
                type: 'contradiction',
                label: 'Conflicting timeframe',
                note: `Specifies "${mA[0].trim()}"`,
              },
            ],
            spansB: [
              {
                start: startB,
                end: endB,
                type: 'contradiction',
                label: 'Conflicting timeframe',
                note: `Specifies "${mB[0].trim()}"`,
              },
            ],
            explanation: `Clause ${clauseA.index} specifies "${mA[0].trim()}" whereas Clause ${clauseB.index} specifies "${mB[0].trim()}" for ${topic}. The contract specifies conflicting operational deadlines that create acute breach risk.`,
            detailedReason: `Parties cannot concurrently fulfill both timeframes. Performing in accordance with one clause directly triggers default under the opposing clause.`,
            remedySuggestion: `Harmonize both provisions into a single governing timeline or define an express order of precedence in the interpretation clause.`,
          };
        }
      }
    }
  }

  // -------------------------------------------------------------
  // Strategy 2: Check for Mutually Exclusive Legal Antonyms & Integration Conflicts
  // -------------------------------------------------------------
  for (const rule of ANTONYM_RULES) {
    const matchA_1 = textA.match(rule.a);
    const matchB_2 = textB.match(rule.b);

    if (matchA_1 && matchB_2) {
      const idxA = textA.indexOf(matchA_1[0]);
      const idxB = textB.indexOf(matchB_2[0]);

      if (idxA !== -1 && idxB !== -1) {
        const phraseA = extractOperativePhrase(textA, idxA, idxA + matchA_1[0].length);
        const phraseB = extractOperativePhrase(textB, idxB, idxB + matchB_2[0].length);

        return {
          clauseAIndex: clauseA.index,
          clauseBIndex: clauseB.index,
          score,
          topic: rule.topic,
          conflictType: 'MUTUAL_EXCLUSIVE',
          hasExactSpans: true,
          spansA: [
            {
              start: phraseA.start,
              end: phraseA.end,
              type: 'contradiction',
              label: 'Opposing standard',
              note: `Specifies ${rule.descA}`,
            },
          ],
          spansB: [
            {
              start: phraseB.start,
              end: phraseB.end,
              type: 'contradiction',
              label: 'Opposing standard',
              note: `Specifies ${rule.descB}`,
            },
          ],
          explanation: `Direct conflict in ${rule.topic}: Clause ${clauseA.index} establishes "${phraseA.text.slice(0, 90)}..." while Clause ${clauseB.index} stipulates "${phraseB.text.slice(0, 90)}...". These legal standards are mutually incompatible.`,
          detailedReason: `The agreement simultaneously affirms and denies ${rule.topic}, rendering enforcement unpredictable in arbitration or litigation.`,
          remedySuggestion: `Delete one of the conflicting standards and confirm the intended legal baseline across both clauses.`,
        };
      }
    }

    // Inverted direction (A matches b, B matches a)
    const matchA_2 = textA.match(rule.b);
    const matchB_1 = textB.match(rule.a);

    if (matchA_2 && matchB_1) {
      const idxA = textA.indexOf(matchA_2[0]);
      const idxB = textB.indexOf(matchB_1[0]);

      if (idxA !== -1 && idxB !== -1) {
        const phraseA = extractOperativePhrase(textA, idxA, idxA + matchA_2[0].length);
        const phraseB = extractOperativePhrase(textB, idxB, idxB + matchB_1[0].length);

        return {
          clauseAIndex: clauseA.index,
          clauseBIndex: clauseB.index,
          score,
          topic: rule.topic,
          conflictType: 'MUTUAL_EXCLUSIVE',
          hasExactSpans: true,
          spansA: [
            {
              start: phraseA.start,
              end: phraseA.end,
              type: 'contradiction',
              label: 'Opposing standard',
              note: `Specifies ${rule.descB}`,
            },
          ],
          spansB: [
            {
              start: phraseB.start,
              end: phraseB.end,
              type: 'contradiction',
              label: 'Opposing standard',
              note: `Specifies ${rule.descA}`,
            },
          ],
          explanation: `Direct conflict in ${rule.topic}: Clause ${clauseA.index} stipulates "${phraseA.text.slice(0, 90)}..." whereas Clause ${clauseB.index} establishes "${phraseB.text.slice(0, 90)}...".`,
          detailedReason: `The agreement simultaneously affirms and negates ${rule.topic}, creating an intractable enforceability deadlock.`,
          remedySuggestion: `Align both clauses to a uniform standard before execution.`,
        };
      }
    }
  }

  // -------------------------------------------------------------
  // Strategy 3: Check for Operative Divergence on Shared Legal Premise
  // (e.g. C003 vs C004: Restraint of trade valid vs void)
  // -------------------------------------------------------------
  const sentencesA = splitSentences(textA);
  const sentencesB = splitSentences(textB);

  for (const sA of sentencesA) {
    for (const sB of sentencesB) {
      const wordsA = sA.text.toLowerCase().replace(/[^a-z0-9\s]/g, '').split(/\s+/).filter(Boolean);
      const wordsB = sB.text.toLowerCase().replace(/[^a-z0-9\s]/g, '').split(/\s+/).filter(Boolean);

      if (wordsA.length >= 5 && wordsB.length >= 4) {
        const setB = new Set(wordsB);
        const shared = wordsA.filter((w) => setB.has(w));
        const sharedRatio = (2 * shared.length) / (wordsA.length + wordsB.length);

        if (sharedRatio >= 0.38) {
          const posA = sA.text.match(POSITIVE_OBLIGATION);
          const negA = sA.text.match(NEGATIVE_PROHIBITION);
          const posB = sB.text.match(POSITIVE_OBLIGATION);
          const negB = sB.text.match(NEGATIVE_PROHIBITION);

          const hasPolarityMismatch = (posA && negB) || (negA && posB);

          if (hasPolarityMismatch) {
            const spanWordA = (posA ? posA[0] : negA ? negA[0] : '').trim();
            const spanWordB = (negB ? negB[0] : posB ? posB[0] : '').trim();

            const idxA = sA.text.indexOf(spanWordA);
            const idxB = sB.text.indexOf(spanWordB);

            const phraseA = extractOperativePhrase(textA, sA.start + (idxA !== -1 ? idxA : 0), sA.start + (idxA !== -1 ? idxA + spanWordA.length : sA.text.length));
            const phraseB = extractOperativePhrase(textB, sB.start + (idxB !== -1 ? idxB : 0), sB.start + (idxB !== -1 ? idxB + spanWordB.length : sB.text.length));

            const topic = sharedSubject || 'contractual obligation & validity';

            return {
              clauseAIndex: clauseA.index,
              clauseBIndex: clauseB.index,
              score,
              topic,
              conflictType: 'PREMISE_DIVERGENCE',
              hasExactSpans: true,
              spansA: [
                {
                  start: phraseA.start,
                  end: phraseA.end,
                  type: 'contradiction',
                  label: 'Conflicting legal outcome',
                },
              ],
              spansB: [
                {
                  start: phraseB.start,
                  end: phraseB.end,
                  type: 'contradiction',
                  label: 'Conflicting legal outcome',
                },
              ],
              explanation: `Clauses share a foundational premise concerning ${topic}, but mandate contradictory legal consequences: Clause ${clauseA.index} provides "${phraseA.text}" whereas Clause ${clauseB.index} mandates "${phraseB.text}".`,
              detailedReason: `One provision creates an affirmative right or validates an obligation, while the other declares it prohibited, void, or penal.`,
              remedySuggestion: `Review against applicable statutory mandates (e.g. Indian Contract Act) and reconcile the operative legal effect.`,
            };
          }
        }
      }
    }
  }

  // -------------------------------------------------------------
  // Strategy 4: Polarity Mismatch Across Detected Contradictory Clauses
  // -------------------------------------------------------------
  const matchPosA = textA.match(POSITIVE_OBLIGATION);
  const matchNegA = textA.match(NEGATIVE_PROHIBITION);
  const matchPosB = textB.match(POSITIVE_OBLIGATION);
  const matchNegB = textB.match(NEGATIVE_PROHIBITION);

  const polarityMismatch = (matchPosA && matchNegB) || (matchNegA && matchPosB);

  if (polarityMismatch) {
    const wordA = (matchPosA ? matchPosA[0] : matchNegA ? matchNegA[0] : '').trim();
    const wordB = (matchNegB ? matchNegB[0] : matchPosB ? matchPosB[0] : '').trim();

    const idxA = textA.indexOf(wordA);
    const idxB = textB.indexOf(wordB);

    if (idxA !== -1 && idxB !== -1) {
      const phraseA = extractOperativePhrase(textA, idxA, idxA + wordA.length);
      const phraseB = extractOperativePhrase(textB, idxB, idxB + wordB.length);
      const topic = sharedSubject || 'contractual remedies & obligations';

      return {
        clauseAIndex: clauseA.index,
        clauseBIndex: clauseB.index,
        score,
        topic,
        conflictType: 'POLARITY',
        hasExactSpans: true,
        spansA: [
          {
            start: phraseA.start,
            end: phraseA.end,
            type: 'contradiction',
            label: 'Conflicting obligation / remedy',
            note: `Operative term: "${wordA}"`,
          },
        ],
        spansB: [
          {
            start: phraseB.start,
            end: phraseB.end,
            type: 'contradiction',
            label: 'Conflicting restriction / disclaimer',
            note: `Operative term: "${wordB}"`,
          },
        ],
        explanation: `Opposing legal obligations on ${topic}: Clause ${clauseA.index} specifies "${phraseA.text}", whereas Clause ${clauseB.index} establishes "${phraseB.text}".`,
        detailedReason: `The party cannot perform its duties or exercise remedies under Clause ${clauseA.index} without simultaneously incurring non-compliance or breach of Clause ${clauseB.index}.`,
        remedySuggestion: `Harmonize both provisions into a single governing clause or add an explicit order-of-precedence clause to clarify which provision prevails.`,
      };
    }
  }

  // -------------------------------------------------------------
  // Strategy 5: Semantic Keyword Isolation for High-Confidence Pairs
  // -------------------------------------------------------------
  if (score >= 0.70) {
    // If backend gave >= 70% confidence, isolate the most operative sentences in each
    const firstA = sentencesA.find((s) => POSITIVE_OBLIGATION.test(s.text) || NEGATIVE_PROHIBITION.test(s.text)) || sentencesA[0];
    const firstB = sentencesB.find((s) => NEGATIVE_PROHIBITION.test(s.text) || POSITIVE_OBLIGATION.test(s.text)) || sentencesB[0];

    if (firstA && firstB) {
      const topic = sharedSubject || 'contractual obligations';
      return {
        clauseAIndex: clauseA.index,
        clauseBIndex: clauseB.index,
        score,
        topic,
        conflictType: 'GENERAL_TENSION',
        hasExactSpans: true,
        spansA: [
          {
            start: firstA.start,
            end: firstA.end,
            type: 'contradiction',
            label: 'Operative conflicting clause',
          },
        ],
        spansB: [
          {
            start: firstB.start,
            end: firstB.end,
            type: 'contradiction',
            label: 'Opposing condition',
          },
        ],
        explanation: `Direct conflict in ${topic}: Clause ${clauseA.index} specifies "${firstA.text.trim().slice(0, 90)}..." while Clause ${clauseB.index} specifies "${firstB.text.trim().slice(0, 90)}...". These provisions create contradictory obligations with ${(score * 100).toFixed(0)}% confidence.`,
        detailedReason: `Operating under both provisions concurrently creates acute commercial exposure and potential contract breach.`,
        remedySuggestion: `Review the highlighted statements side-by-side and align their legal effects prior to signature.`,
      };
    }
  }

  // -------------------------------------------------------------
  // Strategy 6: Conservative Fallback
  // -------------------------------------------------------------
  const fallbackTopic = sharedSubject || 'contractual terms';
  const confidencePercent = (score * 100).toFixed(0);

  return {
    clauseAIndex: clauseA.index,
    clauseBIndex: clauseB.index,
    score,
    topic: fallbackTopic,
    conflictType: 'GENERAL_TENSION',
    hasExactSpans: false,
    spansA: [],
    spansB: [],
    explanation: `Semantic tension detected between Clause ${clauseA.index} and Clause ${clauseB.index} concerning ${fallbackTopic} (${confidencePercent}% model confidence). Exact contradictory sub-phrases were not isolated deterministically; full clauses are shown below for holistic drafting review.`,
    detailedReason: relevantExplanation
      ? `AI Risk Analysis suggests operational tension in clause commitments: ${relevantExplanation.explanation.slice(0, 180)}...`
      : `High semantic similarity between opposing clauses suggests potential overlap or conflicting obligations. Review complete wording to confirm drafting intent.`,
    remedySuggestion: `Review both clauses side-by-side to ensure harmonious obligations across all contract exhibits.`,
  };
}
