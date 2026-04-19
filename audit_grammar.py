import re
import sys

def audit_grammar(file_path):
    # Patterns that identify the Template Parser output
    patterns = {
        "grammar_element": re.compile(r"(Literal|Atomic|Tag|Rule|Sequence|Choice|Repetition|Space)"),
        "trigger": re.compile(r"Grammar still awaiting trigger"),
    }

    grammar_lines = 0
    total_lines = 0
    trigger_warnings = 0
    
    print(f"\nLOG VOLUME & TEMPLATE AUDIT")
    print("=" * 60)

    try:
        with open(file_path, 'r') as f:
            for line in f:
                total_lines += 1
                if patterns["grammar_element"].search(line):
                    grammar_lines += 1
                if patterns["trigger"].search(line):
                    trigger_warnings += 1

        percentage = (grammar_lines / total_lines) * 100 if total_lines > 0 else 0
        
        print(f"LOG VOLUME SUMMARY:")
        print(f"  Total Lines in Log:      {total_lines}")
        print(f"  Template Parser Lines:   {grammar_lines}")
        print(f"  Awaiting Trigger Warns:  {trigger_warnings}")
        print("-" * 30)
        print(f"  Grammar Log Overhead:    {percentage:.2f}%")
        
        print("-" * 30)
        print("INTERPRETATION:")
        if percentage > 80:
            print("  [!] Overhead: EXTREME. The Jinja2 parser is flooding the logs.")
            print("      This contributes to the 'spiky' load via Disk IO.")
        elif percentage > 50:
            print("  [!] Overhead: HIGH. Most of your log storage is template logic.")
        else:
            print("  [✓] Overhead: NORMAL. Log volume is dominated by compute events.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    audit_grammar("logs/server.log")
