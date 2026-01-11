#!/usr/bin/env python3
"""Fix the syntax error in orchestrator.py"""

import re

# Read the file
with open('/home/hieutt50/projects/handoffkit/handoffkit/core/orchestrator.py', 'r') as f:
    content = f.read()

# Find all occurrences of triple quotes
triple_quotes = list(re.finditer(r'"""', content))
print(f"Found {len(triple_quotes)} triple quotes")

# Check if we have an even number (should be pairs)
if len(triple_quotes) % 2 != 0:
    print("Found unpaired triple quote!")

    # Find the last one
    last_quote = triple_quotes[-1]
    line_num = content[:last_quote.start()].count('\n') + 1
    print(f"Last unpaired quote at line {line_num}")

    # Show context
    start = max(0, last_quote.start() - 200)
    end = min(len(content), last_quote.end() + 200)
    context = content[start:end]
    print("\nContext:")
    print(context)
else:
    print("All triple quotes are paired")

# Let's check the specific function around line 1123
lines = content.split('\n')
start_line = 1115
end_line = 1140

print(f"\nLines {start_line}-{end_line}:")
for i in range(start_line-1, end_line):
    if i < len(lines):
        print(f"{i+1:4d}: {lines[i]}")

# Check if there's a malformed docstring
func_start = None
for i, line in enumerate(lines):
    if 'def _format_conversation_summary' in line:
        func_start = i
        break

if func_start:
    print(f"\nFunction starts at line {func_start + 1}")

    # Find the docstring
    docstring_start = None
    docstring_end = None

    for i in range(func_start, min(func_start + 20, len(lines))):
        if '"""' in lines[i]:
            if docstring_start is None:
                docstring_start = i
            else:
                docstring_end = i
                break

    if docstring_start and docstring_end:
        print(f"Docstring from line {docstring_start + 1} to {docstring_end + 1}")
    else:
        print("Could not find complete docstring")

        # Try to fix by adding closing quotes
        if docstring_start and not docstring_end:
            print("Attempting to fix by adding closing quotes...")

            # Find where to add the closing quotes (before the first non-indented line after docstring_start)
            for i in range(docstring_start + 1, min(docstring_start + 20, len(lines))):
                if lines[i].strip() and not lines[i].startswith('        ') and not lines[i].startswith('\t'):
                    # Insert closing quotes before this line
                    lines.insert(i, '        """')
                    break

            # Write back
            new_content = '\n'.join(lines)
            with open('/home/hieutt50/projects/handoffkit/handoffkit/core/orchestrator.py', 'w') as f:
                f.write(new_content)

            print("Fixed! Added closing quotes")