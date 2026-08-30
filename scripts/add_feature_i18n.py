"""Insert research/study/create i18n sections into every locale file.

Keeps the 14 locale files key-parity compliant (the runtime parity test requires
all locales to expose the exact same key set as en-US). Values are English-first
for the new feature surfaces.
"""

from pathlib import Path

LOCALES_DIR = Path("frontend/src/lib/locales")

BLOCK = """  research: {
    title: "Research",
    subtitle: "Generate a source-cited report from your knowledge base.",
    placeholder: "What would you like to research?",
    start: "Start research",
    generating: "Researching…",
    error: "Research failed. Please try again.",
    draft: "Report",
    claims: "Verified claims",
    evidence: "Evidence",
    none: "No claims were extracted.",
    verified: "Verified",
    external: "External",
    inferred: "Inferred",
    unverified: "Unverified",
  },
  study: {
    title: "Study",
    subtitle: "Turn any source into a study plan, quiz, and flashcards.",
    sourceLabel: "Source content",
    sourcePlaceholder: "Paste the text you want to study…",
    generate: "Generate material",
    generating: "Generating…",
    error: "Failed to generate study material.",
    plan: "Study plan",
    explanation: "Explanation",
    quiz: "Quiz",
    flashcards: "Flashcards",
    question: "Question",
    answer: "Answer",
    front: "Front",
    back: "Back",
  },
  create: {
    title: "Create",
    subtitle: "Create new content from your knowledge.",
    summary: "Summary",
    summaryDesc: "Summarize a source into key points.",
    report: "Report",
    reportDesc: "Generate a source-cited research report.",
    presentation: "Presentation",
    presentationDesc: "Build an outline for a talk.",
    quiz: "Quiz",
    quizDesc: "Generate a quiz from your notes.",
    flashcards: "Flashcards",
    flashcardsDesc: "Generate flashcards from your notes.",
    podcast: "Podcast",
    podcastDesc: "Generate a podcast episode.",
  },
"""

ANCHOR = "  home: {"


def main() -> int:
    changed = 0
    for index_file in sorted(LOCALES_DIR.glob("*/index.ts")):
        text = index_file.read_text(encoding="utf-8")
        if "  research: {" in text:
            print(f"skip (already has research): {index_file}")
            continue
        if ANCHOR not in text:
            print(f"WARN: anchor not found in {index_file}")
            continue
        text = text.replace(ANCHOR, BLOCK + ANCHOR, 1)
        index_file.write_text(text, encoding="utf-8")
        changed += 1
        print(f"updated: {index_file}")
    print(f"\n{changed} file(s) updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
