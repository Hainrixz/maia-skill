#!/usr/bin/env bash
# Tododeia / MAIA Skill — Installer
# Usage: curl -sL https://raw.githubusercontent.com/Hainrixz/maia-skill/main/install.sh | bash

set -euo pipefail

REPO="https://github.com/Hainrixz/maia-skill.git"
SKILL_NAME="investment-analysis"
INSTALL_DIR="$HOME/.claude/skills/$SKILL_NAME"
CLONE_DIR="$HOME/.claude/plugins/maia-skill"
RETRY="rm -rf \"$INSTALL_DIR\" \"$CLONE_DIR\" && curl -sL https://raw.githubusercontent.com/Hainrixz/maia-skill/main/install.sh | bash"
CREATED_THIS_RUN=0

cleanup() {
  if [ "$CREATED_THIS_RUN" = "1" ]; then
    echo "  Installation failed — removing partial install..."
    rm -rf "$CLONE_DIR" "$INSTALL_DIR"
  fi
  echo "  To retry: $RETRY"
}
trap cleanup ERR INT

echo ""
echo "  Tododeia — Multi-Agent Investment Analysis"
echo "  by @soyenriquerocha"
echo ""

# Repair a dangling symlink, or update an existing install.
if [ -L "$INSTALL_DIR" ] && [ ! -e "$INSTALL_DIR" ]; then
  echo "  Repairing broken skill symlink..."
  rm -f "$INSTALL_DIR"
elif [ -d "$CLONE_DIR/.git" ]; then
  echo "  Already installed — updating..."
  if git -C "$CLONE_DIR" pull --quiet; then
    echo "  Updated successfully."
  else
    echo "  WARNING: 'git pull' failed; existing install left untouched."
  fi
  echo ""
  trap - ERR INT
  exit 0
fi

# Clone (only if not already present).
echo "  Cloning skill..."
mkdir -p "$HOME/.claude/plugins"
if [ ! -d "$CLONE_DIR/.git" ]; then
  CREATED_THIS_RUN=1
  git clone --quiet "$REPO" "$CLONE_DIR"
fi

# Symlink the skill into Claude Code's skills directory (-n avoids dereferencing an existing dir symlink).
mkdir -p "$HOME/.claude/skills"
ln -sfn "$CLONE_DIR/.claude/skills/$SKILL_NAME" "$INSTALL_DIR"

# Install dashboard dependencies if Node is available (non-fatal — HTML fallback works without it).
if command -v npm >/dev/null 2>&1; then
  echo "  Installing dashboard dependencies..."
  if npm install --prefix "$CLONE_DIR/dashboard" --no-audit --no-fund; then
    echo "  Dashboard ready."
  else
    echo "  WARNING: dashboard dependency install failed (see output above)."
    echo "  The skill will use the HTML fallback report instead."
  fi
else
  echo "  Node.js not found — the skill will use the HTML fallback report."
  echo "  Install Node.js 18+ for the interactive dashboard."
  command -v python3 >/dev/null 2>&1 || echo "  Note: the HTML fallback server needs python3 (not found)."
fi

trap - ERR INT
CREATED_THIS_RUN=0

echo ""
echo "  Installed successfully!"
echo ""
echo "  Optional: set FINNHUB_API_KEY or POLYGON_API_KEY for premium stock data."
echo "  (Free keyless sources — CoinGecko, Yahoo, Frankfurter — are used by default.)"
echo ""
echo "  Open Claude Code and say:"
echo "    \"Run an investment analysis\"  |  \"Analiza los mercados\"  |  \"Run tododeia\""
echo ""
echo "  To uninstall:  rm -rf \"$INSTALL_DIR\" \"$CLONE_DIR\""
echo ""
