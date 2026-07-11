#!/usr/bin/env bash
# Repo foundation engine: gives every published tool a real, findable GitHub repo.
# For each PyPI package: download sdist -> extract -> create repo via API -> push source + store-linked README.
set -u
TOK=$(cat /c/Users/Admin/AppData/Local/hermes/credentials/.github-token)
ROOT=/d/aitest/repo_build
mkdir -p "$ROOT"
cd "$ROOT"

# package -> repo name (under CodeGero/)
declare -A PKG=(
  [kryptorious-devflow]=devflow
  [kryptorious-metaguard]=metaguard
  [kryptorious-csvclean]=csvclean
  [kryptorious-testforge]=testforge
  [kryptorious-envguard]=envguard
  [kryptorious-gitsweep]=gitsweep
  [kryptorious-dataforge]=dataforge
  [kryptorious-jsonguard]=jsonguard
  [kryptorious-depguard]=depguard
)
STORE="https://codegero.github.io/store/"

for pkg in "${!PKG[@]}"; do
  repo="${PKG[$pkg]}"
  echo "===== $pkg -> CodeGero/$repo ====="
  # skip if repo already exists
  code=$(curl -s --max-time 12 -H "Authorization: token $TOK" -o /dev/null -w "%{http_code}" "https://api.github.com/repos/CodeGero/$repo")
  if [ "$code" = "200" ]; then echo "  exists, skip"; continue; fi
  # fetch sdist url
  sdist=$(curl -s --max-time 20 "https://pypi.org/pypi/$pkg/json" | python -c "import sys,json;d=json.load(sys.stdin);print([u['url'] for u in d.get('urls',[]) if u['packagetype']=='sdist'][0])")
  echo "  sdist: $sdist"
  rm -rf "$repo" && mkdir "$repo" && cd "$repo"
  curl -sL --max-time 40 "$sdist" -o src.tar.gz
  tar xzf src.tar.gz --strip-components=1 2>/dev/null || tar xzf src.tar.gz
  rm -f src.tar.gz
  # write README linked to store
  cat > README.md <<EOF
# $pkg

Part of the Kryptorious developer-tools suite (32 free MIT-licensed tools).

## Install
\`\`\`bash
pip install $pkg
\`\`\`

## Source
This repository hosts the published source for \`$pkg\`.

## Premium bundle
Get the full 32-tool bundle with DevFlow Premium (multi-env CI, approval gates, infra-as-code):
👉 $STORE
EOF
  git init -q && git add -A && git -c user.email=bot@kryptorious.dev -c user.name=Kryptorious commit -qm "Initial source for $pkg"
  # create repo via API
  curl -s --max-time 20 -X POST -H "Authorization: token $TOK" -H "Accept: application/vnd.github+json" \
    -d "{\"name\":\"$repo\",\"description\":\"$pkg — Kryptorious developer tool\",\"homepage\":\"$STORE\",\"license\":\"mit\",\"auto_init\":false}" \
    "https://api.github.com/user/repos" -o /tmp/cr.json -w "  create HTTP %{http_code}\n"
  # push
  git remote add origin "https://$TOK@github.com/CodeGero/$repo.git" 2>/dev/null
  git branch -M main 2>/dev/null
  git push -q origin main 2>&1 | tail -1
  cd "$ROOT"
done
echo "DONE"