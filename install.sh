#!/usr/bin/env bash
# Power BI Dashboard Generator — skills installer (macOS / Linux / WSL)
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/bcastelino/powerbi-dashboard-generator/main/install.sh | bash
#
# Optional: pick a target directory (defaults to ~/.claude/skills)
#   curl -fsSL https://raw.githubusercontent.com/bcastelino/powerbi-dashboard-generator/main/install.sh | bash -s -- ~/.windsurf/skills
#
# Common targets:
#   ~/.claude/skills           Claude Code / Claude Desktop
#   ~/.codeium/windsurf/skills Windsurf / Cascade (global)
#   ./.github/skills           GitHub Copilot (repo-local, microsoft/skills convention)

set -euo pipefail

REPO_OWNER="bcastelino"
REPO_NAME="powerbi-dashboard-generator"
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}.git"
REPO_DIR="${HOME}/.${REPO_NAME}"
TARGET="${1:-${HOME}/.claude/skills}"

c_green=$'\033[0;32m'
c_blue=$'\033[0;34m'
c_dim=$'\033[2m'
c_reset=$'\033[0m'

printf "%s→ Installing %s skills%s\n" "$c_blue" "$REPO_NAME" "$c_reset"
printf "  %srepo:   %s%s\n" "$c_dim" "$REPO_URL" "$c_reset"
printf "  %starget: %s%s\n" "$c_dim" "$TARGET" "$c_reset"

# 1. Clone or update the source checkout
if [ -d "${REPO_DIR}/.git" ]; then
  printf "→ Updating existing checkout in %s\n" "$REPO_DIR"
  git -C "${REPO_DIR}" pull --ff-only --quiet
else
  printf "→ Cloning into %s\n" "$REPO_DIR"
  git clone --depth 1 --quiet "${REPO_URL}" "${REPO_DIR}"
fi

# 2. Ensure target directory exists
mkdir -p "${TARGET}"

# 3. Symlink each skill into the target directory
count=0
for skill_dir in "${REPO_DIR}"/skills/*/; do
  name="$(basename "${skill_dir}")"
  dest="${TARGET}/${name}"
  if [ -L "${dest}" ] || [ -e "${dest}" ]; then
    printf "  %s✓%s %s %s(already present, skipping)%s\n" "$c_green" "$c_reset" "$name" "$c_dim" "$c_reset"
    continue
  fi
  ln -s "${skill_dir%/}" "${dest}"
  printf "  %s✓%s %s\n" "$c_green" "$c_reset" "$name"
  count=$((count + 1))
done

# 4. Install Python dependencies if pip is available
echo ""
if command -v pip >/dev/null 2>&1; then
  printf "→ Installing Python dependencies\n"
  pip install --quiet -r "${REPO_DIR}/requirements.txt" || \
    printf "  %s!%s pip install failed — run it manually: pip install -r %s/requirements.txt\n" "$c_dim" "$c_reset" "$REPO_DIR"
else
  printf "  %s!%s pip not found — install Python deps manually: pip install -r %s/requirements.txt\n" "$c_dim" "$c_reset" "$REPO_DIR"
fi

echo ""
printf "%s✓ Installed %d new skills to %s%s\n" "$c_green" "$count" "$TARGET" "$c_reset"
echo ""
echo "Next steps:"
echo "  1. Restart your agent runtime (Claude Code, Windsurf, etc.)"
echo "  2. Ask the agent: 'List the skills you have available'"
echo "  3. Try it: 'Build me a sales dashboard from sales.xlsx'"
