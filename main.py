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

ROOT = Path(__file__).parent
INP = ROOT / "sample_inputs"
OUT = ROOT / "outputs"
PROMPT = (ROOT / "prompt.md").read_text(encoding="utf-8")

# --- Чтение входных данных ---
def read_inputs() -> Dict[str, str]:
    jd = (INP / "jd.txt").read_text(encoding="utf-8")
    cvs = {}
    for name in ["cv1.txt", "cv2.txt", "cv3.txt"]:
        cvs[name] = (INP / name).read_text(encoding="utf-8")
    return {"jd": jd, "cvs": cvs}

# --- Базовый анализ (если нет ключа Gemini) ---
def baseline_score(jd: str, cv: str) -> CVScore:
    tok = lambda s: {w.lower() for w in re.findall(r"[a-zA-ZāčēģīķļņšūžА-Яа-я0-9+#\.]+", s)}
    jd_tokens = tok(jd)
    cv_tokens = tok(cv)
    overlap = len(jd_tokens & cv_tokens)
    recall = overlap / max(1, len(jd_tokens))
    precision = overlap / max(1, len(cv_tokens))
    f1 = 0 if (precision + recall) == 0 else 2 * precision * recall / (precision + recall)
    score = min(100, int(round(f1 * 120)))

    strengths = sorted(list(jd_tokens & cv_tokens))[:10]
    missing = sorted(list(jd_tokens - cv_tokens))[:10]
    verdict = "strong match" if score >= 80 else ("possible match" if score >= 50 else "not a match")
    summary = f"Baseline overlap score={score}. Overlap {overlap} common words."
    return CVScore(match_score=score, summary=summary, strengths=strengths, missing_requirements=missing, verdict=verdict)

# --- Попытка использовать Gemini ---
def try_gemini(jd: str, cv: str) -> CVScore:
    try:
        from llm_providers.gemini import GeminiClient
        client = GeminiClient()
        raw = client.infer(PROMPT, jd, cv)
        data = json.loads(raw)
        return CVScore(**data)
    except Exception as e:
        print(f"[yellow]Gemini unavailable → fallback mode. Reason: {e}[/yellow]")
        return baseline_score(jd, cv)

# --- Шаблон для отчёта ---
REPORT_TMPL = Template("""
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

# --- Сохранение результатов ---
def save_outputs(scores: Dict[str, CVScore]):
    OUT.mkdir(exist_ok=True, parents=True)
    for name, s in scores.items():
        (OUT / f"{name}.json").write_text(
            json.dumps(s.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
    md = REPORT_TMPL.render(scores=scores)
    (OUT / "CV_report.md").write_text(md, encoding="utf-8")
    html = markdown.markdown(md, extensions=["tables"])
    soup = BeautifulSoup(html, "html.parser")
    (OUT / "CV_report.html").write_text(str(soup), encoding="utf-8")

# --- Главная функция ---
def main():
    data = read_inputs()
    jd = data["jd"]
    cvs = data["cvs"]

    results = {}
    for filename, content in cvs.items():
        print(f"[cyan]Processing {filename}...[/cyan]")
        results[filename] = try_gemini(jd, content)

    save_outputs(results)
    print("[green]✅ Done! See outputs/ for JSON and HTML report.[/green]")

if __name__ == "__main__":
    main()
