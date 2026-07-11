#!/usr/bin/env bash
# Repo foundation engine v2: retry-on-400 create, idempotent.
set -u
TOK=$(cat /c/Users/Admin/AppData/Local/hermes/credentials/.github-token)
ROOT=/d/aitest/repo_build
mkdir -p "$ROOT"

create_repo() {
  local repo="$1" desc="$2"
  for i in 1 2 3 4 5; do
    code=$(curl -s --max-time 25 -X POST -H "Authorization: token $TOK" -H "Accept: application/vnd.github+json" \
      -d "{\"name\":\"$repo\",\"description\":\"$desc\",\"homepage\":\"https://codegero.github.io/store/\",\"license\":\"mit\"}" \
      "https://api.github.com/user/repos" -o /tmp/cr.json -w "%{http_code}")
    if [ "$code" = "201" ] || [ "$code" = "200" ]; then return 0; fi
    # if repo already exists (race), treat as ok
    if curl -s --max-time 10 -H "Authorization: token $TOK" -o /dev/null -w "%{http_code}" "https://api.github.com/repos/CodeGero/$repo" | grep -q 200; then return 0; fi
    echo "    create $repo attempt $i -> $code, retrying"; sleep 4
  done
  return 1
}

push_repo() {
  local repo="$1"
  cd "$ROOT/$repo"
  git remote remove origin 2>/dev/null
  git remote add origin "https://$TOK@github.com/CodeGero/$repo.git"
  git branch -M main 2>/dev/null
  git push -q origin main 2>&1 | tail -1
  cd "$ROOT"
}

# package -> repo -> sdist? (only those still missing a repo)
declare -A PKG=(
  [kryptorious-dataforge]=dataforge
  [kryptorious-depguard]=depguard
  [kryptorious-envguard]=envguard
  [kryptorious-gitsweep]=gitsweep
  [kryptorious-jsonguard]=jsonguard
  [kryptorious-metaguard]=metaguard
  [kryptorious-testforge]=testforge
  [kryptorious-devflow]=devflow
)
STORE="https://codegero.github.io/store/"

for pkg in "${!PKG[@]}"; do
  repo="${PKG[$pkg]}"
  echo "===== $pkg -> CodeGero/$repo ====="
  if curl -s --max-time 10 -H "Authorization: token $TOK" -o /dev/null -w "%{http_code}" "https://api.github.com/repos/CodeGero/$repo" | grep -q 200; then
    echo "  repo exists"; push_repo "$repo"; continue
  fi
  sdist=$(curl -s --max-time 20 "https://pypi.org/pypi/$pkg/json" | python -c "import sys,json;d=json.load(sys.stdin);print([u['url'] for u in d.get('urls',[]) if u['packagetype']=='sdist'][0])")
  rm -rf "$ROOT/$repo" && mkdir "$ROOT/$repo" && cd "$ROOT/$repo"
  curl -sL --max-time 40 "$sdist" -o src.tar.gz
  tar xzf src.tar.gz --strip-components=1; rm -f src.tar.gz
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
  if create_repo "$repo" "$pkg — Kryptorious developer tool"; then
    push_repo "$repo"
  else
    echo "  FAILED to create $repo"
  fi
  cd "$ROOT"
done
echo "DONE"