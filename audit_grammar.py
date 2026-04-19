import re
import sys
from collections import Counter

def audit_grammar(file_path):
    patterns = {
        "grammar": re.compile(r"(Literal|Atomic|Tag|Rule|Sequence|Choice|Repetition|Space)"),
        "tool_detect": re.compile(r"\"description\":\"([^\"]*)\""),
        "tool_name": re.compile(r"\"name\":\"([^\"]*)\"")
    }

    stats = {
        "grammar_lines": 0,
        "total_lines": 0,
        "tool_bloat": Counter()
    }
    
    current_tool = "General Template"

    print(f"\nLOG BLOAT & TOOL GRAMMAR AUDIT")
    print("=" * 70)

    try:
        with open(file_path, 'r') as f:
            for line in f:
                stats["total_lines"] += 1
                
                # 1. Detect which tool is being defined
                name_m = patterns["tool_name"].search(line)
                if name_m:
                    current_tool = name_m.group(1)

                # 2. Accounting for grammar dump
                if patterns["grammar"].search(line):
                    stats["grammar_lines"] += 1
                    stats["tool_bloat"][current_tool] += 1

        print(f"LOG VOLUME SUMMARY:")
        print(f"  Total Lines:          {stats['total_lines']:,}")
        print(f"  Grammar Bloat Lines:  {stats['grammar_lines']:,}")
        print(f"  Overall Overhead:     {(stats['grammar_lines']/stats['total_lines'])*100:.2f}%")
        print("-" * 35)
        
        print("BLOAT BY TOOL (Top Contributors):")
        for tool, count in stats["tool_bloat"].most_common(5):
            print(f"  -> {tool.ljust(15)}: {count:,} lines")

        print("-" * 35)
        print("DIAGNOSTIC:")
        if stats["grammar_lines"] > 50000:
            print("  [!] EXTREME BLOAT: Template logs are massive. Recommend lowering verbosity.")
        elif any(count > 1000 for count in stats["tool_bloat"].values()):
            print("  [!] COMPLEX TOOLS: Some tools have huge grammar definitions.")
        else:
            print("  [✓] NORMAL: Tool definitions are within reasonable bounds.")

    except Exception as e:
        print(f"Error during audit: {e}")

if __name__ == "__main__":
    audit_grammar("logs/server.log")
