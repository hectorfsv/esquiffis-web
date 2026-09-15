#!/usr/bin/env bash
# Verify the Esquiffis web page. Read-only: nothing is sent, nothing is spent.
#   ./test/run.sh           every mode at every viewport (Chromium)
#   ./test/run.sh webkit    the lock and chat layout in real WebKit via ../webkit-check
# The harness is REGENERATED from index.html on every run; test/build is disposable.
set -u
cd "$(dirname "$0")/.."
B="$PWD/test/build"; INJ="$PWD/test/inject"; mkdir -p "$B"
CHR="$HOME/Library/Caches/ms-playwright/chromium_headless_shell-1217/chrome-headless-shell-mac-x64/chrome-headless-shell"
[ -x "$CHR" ] || { echo "chrome-headless-shell not found at $CHR"; exit 2; }
python3 - "$INJ/chat.txt" "$B/c.html" <<'PY'
import sys
src=open('index.html').read(); inj=open(sys.argv[1]).read()
assert src.count('</body>')==1
open(sys.argv[2],'w').write(src.replace('</body>', inj+'\n</body>'))
PY
cp hero.webp "$B/hero.webp"
title(){ "$CHR" --headless --disable-gpu --hide-scrollbars --virtual-time-budget="${4:-6000}" \
  --window-size="$1","$2" --dump-dom "$3" 2>/dev/null | tr -d '\n' | sed -n 's/.*<title>§\(.*\)§<\/title>.*/\1/p'; }
WHAT="${1:-all}"; PASS=0; FAIL=0
if [ "$WHAT" = all ] || [ "$WHAT" = chat ]; then
  echo "CHAT  (8 modes x 4 viewports)"
  for m in ok badpw expired persist guard hub hubfail timeout; do
    for v in "393 700" "393 852" "852 393" "2026 1037"; do set -- $v
      budget=8000; [ "$m" = timeout ] && budget=140000
      R=$(title "$1" "$2" "file://$B/c.html?t=$m" $budget)
      p=$(printf '%s' "$R" | grep -o PASS | wc -l | tr -d ' '); f=$(printf '%s' "$R" | grep -o FAIL | wc -l | tr -d ' ')
      PASS=$((PASS+p)); FAIL=$((FAIL+f))
      [ -z "$R" ] && { FAIL=$((FAIL+1)); echo "  t=$m ${1}x${2}: NO RESULT (harness never reported)"; }
      [ "$f" != 0 ] && { echo "  t=$m ${1}x${2}"; printf '%s' "$R" | sed 's/FAIL/\nFAIL/g' | grep FAIL | sed 's/^/     /'; }
    done
  done
  echo "  -> $PASS pass / $FAIL fail"
fi
if [ "$WHAT" = webkit ]; then
  node ../webkit-check/check.js "file://$PWD/index.html" --out "$B/shots"
fi
[ "$FAIL" = 0 ] && echo "ALL GREEN — $PASS assertions, 0 failures" || { echo "FAILURES: $FAIL"; exit 1; }
