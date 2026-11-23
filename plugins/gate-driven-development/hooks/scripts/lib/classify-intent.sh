#!/usr/bin/env bash
# Shared intent classifier for GDD scripts and hooks.
# Source this file — do not execute directly.
#
# Mirrors references/entry-intent.md (shell-level heuristic).
# Final intent resolution is still performed by gdd-brainstorming.
#
# Usage:
#   source "$PLUGIN_ROOT/hooks/scripts/lib/classify-intent.sh"
#   intent="$(gdd_classify_intent "$user_text")"
#   # intent ∈ { new, resume, ambiguous }

gdd_has_concrete_task_text() {
  local text="$1"
  if [[ -z "${text//[[:space:]]/}" ]]; then
    return 1
  fi

  # URL-only input is ambiguous. URLs can be supporting context, but a bare URL
  # does not say what to change or investigate.
  if [[ "$text" =~ ^[[:space:]]*https?://[^[:space:]]+[[:space:]]*$ ]]; then
    return 1
  fi

  case "$text" in
    *したい*|*してほしい*|*してください*|*して*|*する*|*した*|*ほしい*|*必要*|*判断したい*|*確認して*|*調査して*|*調査したい*|*修正*|*改善*|*追加*|*削除*|*作成*|*実装*|*変更*|*整理*|*確認*|*調査*|*判断*|*fix*|*Fix*|*implement*|*Implement*|*add*|*Add*|*update*|*Update*|*improve*|*Improve*|*investigate*|*Investigate*|*check*|*Check*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

gdd_classify_intent() {
  local text="$1"
  if [[ -z "$text" ]]; then
    echo "ambiguous"
    return
  fi
  local has_resume_cue=false
  local has_new_cue=false
  if [[ "$text" == *"再開"* || "$text" == *"続き"* || "$text" == *"続きから"* || "$text" == *"resume"* || "$text" == *"Resume"* ]]; then
    has_resume_cue=true
  fi
  if [[ "$text" == *"新規"* || "$text" == *"新規開始"* || "$text" == *"別件"* || "$text" == *"新しい"* ]]; then
    has_new_cue=true
  fi
  if [[ "$has_resume_cue" == "true" && "$has_new_cue" == "true" ]]; then
    echo "ambiguous"
  elif [[ "$has_resume_cue" == "true" ]]; then
    echo "resume"
  elif [[ "$has_new_cue" == "true" ]]; then
    echo "new"
  elif gdd_has_concrete_task_text "$text"; then
    echo "new"
  else
    # No concrete task intent (e.g. URL-only, unrelated text) → ambiguous, not new.
    echo "ambiguous"
  fi
}
