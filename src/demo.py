import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pipeline import run_agent

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    test_message = "hiii, samera, how are you? have a beuatiful day, and im  a very big fan of your work"
    test_thread_context = test_message  # no prior context for a single fresh message

    result = run_agent(test_message, test_thread_context)

    print("=" * 60)
    print(f"INPUT: {test_message}")
    print("=" * 60)
    print(f"Predicted Intent: {result['intent']}")
    if 'confidence' in result:
        print(f"Confidence: {result['confidence']}")
    print(f"\nDrafted Reply: {result['reply']}")
    print(f"\nEscalate: {result['escalate']}")
    print(f"Reason: {result['escalate_reason']}")
    if 'hallucination_flagged' in result:
        print(f"\nHallucination flagged: {result['hallucination_flagged']}")