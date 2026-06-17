import subprocess
import re
from pathlib import Path

MODEL = "/storage/emulated/0/Download/qwen2.5-1.5b-instruct-q3_k_m.gguf"

def clean_output(out: str) -> str:
    text = out.replace("\r", "")
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    text = re.sub(r"[|/\\-]\x08", "", text)
    text = text.replace("\b", "")

    if "Queen:" in text:
        part = text.rsplit("Queen:", 1)[1]
        if "[ Prompt:" in part:
            part = part.split("[ Prompt:", 1)[0]

        lines = [x.strip() for x in part.splitlines() if x.strip()]
        bad = (
            "common_memory",
            "load_backend:",
            "Loading model",
            "build",
            "model",
            "modalities",
            "available commands",
            "/exit",
            "/regen",
            "/clear",
            "/read",
            "/glob",
            "Exiting",
            "▄▄",
            "██",
            ">",
        )
        lines = [x for x in lines if not x.startswith(bad)]
        ans = "\n".join(lines).strip()
        if ans:
            return ans[-2000:]

    lines = [x.strip() for x in text.splitlines() if x.strip()]
    lines = [
        x for x in lines
        if not x.startswith("common_memory")
        and not x.startswith("load_backend:")
        and not x.startswith("[ Prompt:")
        and not x.startswith("Exiting")
        and not x.startswith("▄▄")
        and not x.startswith("██")
    ]
    return "\n".join(lines).strip()[-2000:]
def queen_answer(prompt: str) -> str:
    if not Path(MODEL).exists():
        return "Queen Intelligence غير متصل: ملف النموذج غير موجود."

    full_prompt = (
        "أنت Queen، عقل داخلي داخل مشروع Gerfex. "
        "أجب عن سؤال المستخدم فقط. "
        "لا تذكر أمثلة سابقة. "
        "لا تكتب كلمة المستخدم. "
        "لا تكرر السؤال. "
        "لا تكتب أي مقدمة. "
        "أجب بالعربية وباختصار مفيد.\\n\\n"
        f"{prompt}\\n"
        "Queen:"
    )

    cmd = (
        'llama-cli '
        f'-m "{MODEL}" '
        f'-p "{full_prompt}" '
        '-n 160 -t 4 -c 768 --no-display-prompt --single-turn'
    )

    r = subprocess.run(
        ["script", "-q", "-c", cmd, "/dev/null"],
        capture_output=True,
        text=True,
        timeout=180
    )

    if r.returncode != 0:
        return "فشل تشغيل Queen Intelligence:\n" + r.stderr[-1200:]

    combined = (r.stdout or "") + "\n" + (r.stderr or "")
    return clean_output(combined) or "Queen لم تنتج ردًا واضحًا."

if __name__ == "__main__":
    import sys
    print(queen_answer(" ".join(sys.argv[1:]) or "ماهي عاصمة السعودية؟"))
