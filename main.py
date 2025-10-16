import os
import json
import re
from pathlib import Path
from typing import Dict
from rich import print
from schemas import CVScore
from jinja2 import Template
import markdown
from bs4 import BeautifulSoup


# --- Define paths ---
ROOT: Path = Path(__file__).parent
INP: Path = ROOT / "sample_inputs"
OUT: Path = ROOT / "outputs"
PROMPT: str = (ROOT / "prompt.md").read_text(encoding="utf-8")


# --- Read input files (Job Description + CVs) ---
def read_inputs() -> Dict[str, str]:
    """
    Reads the Job Description (JD) and candidate CV files from the sample_inputs directory.
    Returns a dictionary with JD text and CV texts.
    """
    jd: str = (INP / "jd.txt").read_text(encoding="utf-8")
    cvs: Dict[str, str] = {}
    for name in ["cv1.txt", "cv2.txt", "cv3.txt"]:
        cvs[name] = (INP / name).read_text(encoding="utf-8")
    return {"jd": jd, "cvs": cvs}


# --- Baseline analysis (used if Gemini is not available) ---
def baseline_score(jd: str, cv: str) -> CVScore:
    """
    Performs a simple keyword-based comparison between JD and CV.
    Calculates overlap and returns a CVScore object with heuristic evaluation.
    """
    # Tokenization: extract alphanumeric words (supports Latvian, Russian, English)
    tok = lambda s: {w.lower() for w in re.findall(r"[a-zA-ZāčēģīķļņšūžА-Яа-я0-9+#\.]+", s)}

    jd_tokens = tok(jd)
    cv_tokens = tok(cv)

    overlap: int = len(jd_tokens & cv_tokens)
    recall: float = overlap / max(1, len(jd_tokens))
    precision: float = overlap / max(1, len(cv_tokens))
    f1: float = 0 if (precision + recall) == 0 else 2 * precision * recall / (precision + recall)
    score: int = min(100, int(round(f1 * 120)))  # slightly optimistic scaling

    strengths: list[str] = sorted(list(jd_tokens & cv_tokens))[:10]
    missing: list[str] = sorted(list(jd_tokens - cv_tokens))[:10]
    verdict: str = (
        "strong match" if score >= 80 else
        ("possible match" if score >= 50 else "not a match")
    )
    summary: str = f"Baseline overlap score={score}. Overlap {overlap} common words."
    return CVScore(
        match_score=score,
        summary=summary,
        strengths=strengths,
        missing_requirements=missing,
        verdict=verdict
    )


# --- Try Gemini API for semantic comparison ---
def try_gemini(jd: str, cv: str) -> CVScore:
    """
    Attempts to call Gemini API for semantic evaluation of the CV.
    Falls back to baseline scoring if API key is missing or request fails.
    """
    try:
        from llm_providers.gemini import GeminiClient
        client = GeminiClient()
        raw: str = client.infer(PROMPT, jd, cv)
        data: dict = json.loads(raw)
        return CVScore(**data)
    except Exception as e:
        print(f"[yellow]Gemini unavailable → fallback mode. Reason: {e}[/yellow]")
        return baseline_score(jd, cv)


# --- Markdown template for the report ---
REPORT_TMPL: Template = Template("""
# AI CV Match Report

**Job Description:** `sample_inputs/jd.txt`

| CV | Match score | Verdict |
|----|-------------|---------|
{% for name, s in scores.items() -%}
| {{name}} | {{s.match_score}} | {{s.verdict}} |
{% endfor %}

---
{% for name, s in scores.items() %}
## {{name}}

**Summary:** {{s.summary}}

**Strengths**
{% for it in s.strengths %}- {{it}}
{% endfor %}

**Missing requirements**
{% for it in s.missing_requirements %}- {{it}}
{% endfor %}

---
{% endfor %}
""")


# --- Save all results ---
def save_outputs(scores: Dict[str, CVScore]) -> None:
    """
    Saves the evaluation results in both JSON and Markdown + HTML formats.
    Automatically creates the outputs directory if it does not exist.
    """
    OUT.mkdir(exist_ok=True, parents=True)

    # Save JSON files for each CV
    for name, s in scores.items():
        (OUT / f"{name}.json").write_text(
            json.dumps(s.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    # Generate Markdown report
    md: str = REPORT_TMPL.render(scores=scores)
    (OUT / "CV_report.md").write_text(md, encoding="utf-8")

    # Convert Markdown to HTML
    html: str = markdown.markdown(md, extensions=["tables"])
    soup: BeautifulSoup = BeautifulSoup(html, "html.parser")
    (OUT / "CV_report.html").write_text(str(soup), encoding="utf-8")


# --- Main function ---
def main() -> None:
    """
    Entry point of the program:
    - Reads JD and CV files
    - Uses Gemini (if available) or baseline comparison
    - Saves structured reports
    """
    data: Dict[str, str] = read_inputs()
    jd: str = data["jd"]
    cvs: Dict[str, str] = data["cvs"]

    results: Dict[str, CVScore] = {}

    for filename, content in cvs.items():
        print(f"[cyan]Processing {filename}...[/cyan]")
        results[filename] = try_gemini(jd, content)

    save_outputs(results)
    print("[green]Done! See outputs/ for JSON and HTML report.[/green]")


if __name__ == "__main__":
    main()
