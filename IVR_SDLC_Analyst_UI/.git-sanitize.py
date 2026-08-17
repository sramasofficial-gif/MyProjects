#!/usr/bin/env python3
import os
import sys

# Sanitizer: replace a leaked token literal with [REDACTED]
LEAK = "[REDACTED_GITHUB_PAT]"
REPLACEMENT = "[REDACTED_GITHUB_PAT]"

def is_text_file(path):
    try:
        with open(path, 'rb') as f:
            data = f.read(4096)
        data.decode('utf-8')
        return True
    except Exception:
        return False

def sanitize_file(path):
    try:
        if is_text_file(path):
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                s = f.read()
            if LEAK in s:
                s2 = s.replace(LEAK, REPLACEMENT)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(s2)
                print(f"Sanitized text: {path}")
        else:
            # binary: if contains bytes of leak, remove file
            with open(path, 'rb') as f:
                data = f.read()
            if LEAK.encode() in data:
                os.remove(path)
                print(f"Removed binary file containing secret: {path}")
    except Exception as e:
        print(f"Error sanitizing {path}: {e}")

def main(root='.'):
    for dirpath, dirnames, filenames in os.walk(root):
        # skip .git
        if '.git' in dirpath.split(os.sep):
            continue
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            sanitize_file(path)

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else '.'
    main(target)
