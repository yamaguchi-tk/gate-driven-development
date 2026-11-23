#!/usr/bin/env bash
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-${HOME}/.claude}"
STATE_DIR="$CLAUDE_HOME/plugins/gate-driven-development"
STATE_FILE="$STATE_DIR/claude-code-links.tsv"
DRY_RUN=false
ENTRY_SOURCES=()
ENTRY_TARGETS=()

usage() {
  echo "Usage: $0 [--dry-run]"
}

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
elif [[ -n "${1:-}" ]]; then
  usage
  exit 1
fi

add_entry() {
  local source_path="$1"
  local target_path="$2"

  ENTRY_SOURCES+=("$source_path")
  ENTRY_TARGETS+=("$target_path")
}

load_entries() {
  local source_path
  local target_path

  if [[ ! -f "$STATE_FILE" ]]; then
    echo "ERROR: state file missing: $STATE_FILE" >&2
    echo "ERROR: rename-safe uninstall requires the saved link state; run manual cleanup if the state file is gone." >&2
    return 1
  fi

  while IFS=$'\t' read -r source_path target_path; do
    [[ -n "$source_path" && -n "$target_path" ]] || continue
    add_entry "$source_path" "$target_path"
  done <"$STATE_FILE"

  if [[ "${#ENTRY_SOURCES[@]}" -eq 0 ]]; then
    echo "ERROR: state file is empty: $STATE_FILE" >&2
    return 1
  fi
}

remove_entry() {
  local source_path="$1"
  local target_path="$2"

  if [[ ! -L "$target_path" ]]; then
    if [[ -e "$target_path" ]]; then
      echo "SKIP: not a symlink: $target_path"
    else
      echo "SKIP: missing: $target_path"
    fi
    return 0
  fi

  if [[ "$(readlink "$target_path")" != "$source_path" ]]; then
    echo "SKIP: symlink not managed by this plugin: $target_path -> $(readlink "$target_path")"
    return 0
  fi

  echo "REMOVE: $target_path"
  if [[ "$DRY_RUN" == "false" ]]; then
    rm "$target_path"
  fi
}

main() {
  local idx

  load_entries

  for idx in "${!ENTRY_SOURCES[@]}"; do
    remove_entry "${ENTRY_SOURCES[$idx]}" "${ENTRY_TARGETS[$idx]}"
  done

  if [[ "$DRY_RUN" == "false" && -f "$STATE_FILE" ]]; then
    rm "$STATE_FILE"
  fi

  echo "DONE: Claude Code symlink removal completed"
}

main "$@"
