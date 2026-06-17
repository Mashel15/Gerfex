from pathlib import Path

q = Path("runtime/android_queue.txt")
q.parent.mkdir(parents=True, exist_ok=True)
q.write_text("", encoding="utf-8")

print("QUEUE CLEARED:", q)
