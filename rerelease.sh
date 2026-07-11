#!/usr/bin/env bash
# Re-release all kryptorious-* PyPI tools with corrected [project.urls] metadata.
# Homepage/Repository now point to real CodeGero repos + the store. Patch version bump.
set -u
ROOT=/d/aitest/repo_rebuild
mkdir -p "$ROOT"
cd "$ROOT"

# pkg -> repo (real CodeGero repo)
declare -A REPO=(
#  [kryptorious-csvclean]=kryptorious-csvclean
  [kryptorious-devflow]=kryptorious-devflow
  [kryptorious-metaguard]=kryptorious-metaguard
  [kryptorious-testforge]=kryptorious-testforge
  [kryptorious-envguard]=kryptorious-envguard
  [kryptorious-gitsweep]=kryptorious-gitsweep
  [kryptorious-dataforge]=kryptorious-dataforge
  [kryptorious-jsonguard]=kryptorious-jsonguard
  [kryptorious-depguard]=kryptorious-depguard
  [kryptorious-apiguard]=apiguard
  [kryptorious-draftguard]=draftguard
)
STORE="https://codegero.github.io/store/"

for pkg in "${!REPO[@]}"; do
  repo="${REPO[$pkg]}"
  echo "===== $pkg (repo: $repo) ====="
  # fetch current version + sdist
  ver=$(curl -s --max-time 20 "https://pypi.org/pypi/$pkg/json" | python -c "import sys,json;print(json.load(sys.stdin)['info']['version'])")
  echo "  current version: $ver"
  # bump patch: 1.1.0 -> 1.1.1
  IFS='.' read -r a b c <<< "$ver"
  newver="$a.$b.$((c+1))"
  echo "  new version: $newver"
  sdist=$(curl -s --max-time 20 "https://pypi.org/pypi/$pkg/json" | python -c "import sys,json;d=json.load(sys.stdin);print([u['url'] for u in d.get('urls',[]) if u['packagetype']=='sdist'][0])")
  rm -rf "$pkg" && mkdir "$pkg" && cd "$pkg"
  curl -sL --max-time 40 "$sdist" -o src.tar.gz
  tar xzf src.tar.gz --strip-components=1; rm -f src.tar.gz
  # patch pyproject: version + urls
  python - "$newver" "$repo" "$STORE" <<'PY'
import sys,re
nv,repo,store=sys.argv[1],sys.argv[2],sys.argv[3]
p='pyproject.toml'
s=open(p,encoding='utf-8').read()
s=re.sub(r'version = "[^"]*"', f'version = "{nv}"', s, count=1)
# replace [project.urls] block
s=re.sub(r'\[project\.urls\][^\[]*',
         f'[project.urls]\nHomepage = "{store}"\nRepository = "https://github.com/CodeGero/{repo}"\nChangelog = "https://github.com/CodeGero/{repo}/releases"\n',
         s)
open(p,'w',encoding='utf-8').write(s)
print("  patched pyproject version+urls")
PY
  rm -rf dist build
  python -m build 2>&1 | tail -1
  echo "  uploading..."
  python -m twine upload --non-interactive dist/* 2>&1 | tail -2
  cd "$ROOT"
done
echo "ALL DONE"