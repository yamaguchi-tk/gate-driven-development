#!/usr/bin/env bash
# Shared helpers for install-claude-code-links.sh and install-cursor-links.sh.
# Source this file after setting PLUGIN_ROOT, TARGET_HOME, STATE_DIR, STATE_FILE.

ENTRY_SOURCES=()
ENTRY_TARGETS=()
CREATED_TARGETS=()

add_entry() {
  local source_path="$1"
  local target_path="$2"

  ENTRY_SOURCES+=("$source_path")
  ENTRY_TARGETS+=("$target_path")
}

has_target_entry() {
  local candidate="$1"
  local target_path

  for target_path in "${ENTRY_TARGETS[@]}"; do
    if [[ "$target_path" == "$candidate" ]]; then
      return 0
    fi
  done

  return 1
}

build_entries() {
  local source_path

  shopt -s nullglob

  for source_path in "$PLUGIN_ROOT"/commands/*.md; do
    add_entry "$source_path" "$TARGET_HOME/commands/$(basename "$source_path")"
  done

  for source_path in "$PLUGIN_ROOT"/agents/*.md; do
    add_entry "$source_path" "$TARGET_HOME/agents/$(basename "$source_path")"
  done

  for source_path in "$PLUGIN_ROOT"/skills/*; do
    [[ -f "$source_path/SKILL.md" ]] || continue
    add_entry "$source_path" "$TARGET_HOME/skills/$(basename "$source_path")"
  done
}

validate_existing_state() {
  local source_path
  local target_path
  local saw_entry=false

  [[ -f "$STATE_FILE" ]] || return 0

  while IFS=$'\t' read -r source_path target_path; do
    [[ -n "$source_path" && -n "$target_path" ]] || continue
    saw_entry=true
    if ! has_target_entry "$target_path"; then
      echo "ERROR: managed target disappeared since the previous install: $target_path" >&2
      echo "ERROR: run uninstall before install when renaming or removing plugin assets." >&2
      return 1
    fi
  done <"$STATE_FILE"

  if [[ "$saw_entry" == "false" ]]; then
    echo "ERROR: state file is empty: $STATE_FILE" >&2
    return 1
  fi
}

check_entry() {
  local source_path="$1"
  local target_path="$2"

  if [[ -L "$target_path" ]]; then
    if [[ "$(readlink "$target_path")" == "$source_path" ]]; then
      echo "OK: already linked $target_path"
      return 0
    fi
    echo "CONFLICT: symlink points elsewhere: $target_path -> $(readlink "$target_path")" >&2
    return 1
  fi

  if [[ -e "$target_path" ]]; then
    echo "CONFLICT: target already exists: $target_path" >&2
    return 1
  fi

  echo "LINK: $target_path -> $source_path"
  return 0
}

preflight() {
  local idx
  local has_conflict=false

  for idx in "${!ENTRY_SOURCES[@]}"; do
    if ! check_entry "${ENTRY_SOURCES[$idx]}" "${ENTRY_TARGETS[$idx]}"; then
      has_conflict=true
    fi
  done

  if [[ "$has_conflict" == "true" ]]; then
    return 1
  fi
}

rollback_created_links() {
  local idx
  local target_path

  for ((idx=${#CREATED_TARGETS[@]} - 1; idx>=0; idx--)); do
    target_path="${CREATED_TARGETS[$idx]}"
    [[ -L "$target_path" ]] || continue
    rm "$target_path" || true
  done
}

write_state_file() {
  local tmp_file
  local idx

  mkdir -p "$STATE_DIR"
  tmp_file="$(mktemp "$STATE_DIR/links.XXXXXX")"

  for idx in "${!ENTRY_SOURCES[@]}"; do
    printf '%s\t%s\n' "${ENTRY_SOURCES[$idx]}" "${ENTRY_TARGETS[$idx]}" >>"$tmp_file"
  done

  mv "$tmp_file" "$STATE_FILE"
}

apply_links() {
  local idx
  local source_path
  local target_path

  trap rollback_created_links ERR

  for idx in "${!ENTRY_SOURCES[@]}"; do
    source_path="${ENTRY_SOURCES[$idx]}"
    target_path="${ENTRY_TARGETS[$idx]}"

    if [[ -L "$target_path" ]] && [[ "$(readlink "$target_path")" == "$source_path" ]]; then
      continue
    fi

    mkdir -p "$(dirname "$target_path")"
    ln -s "$source_path" "$target_path"
    CREATED_TARGETS+=("$target_path")
  done

  write_state_file
  trap - ERR
}

run_install() {
  local label="$1"

  build_entries
  validate_existing_state
  preflight

  if [[ "$DRY_RUN" == "false" ]]; then
    apply_links
  fi

  echo "DONE: ${label} symlink installation completed"
}
