import sys

from learning_companion.chain import PROMPT

question = " ".join(sys.argv[1:]) or "Explain recursion in one line"
for m in PROMPT.format_messages(question=question):
    print(f"[{m.type}] {m.content}")
