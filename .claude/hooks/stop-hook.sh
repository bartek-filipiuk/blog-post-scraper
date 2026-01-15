#!/bin/bash
# Ralph Loop Stop Hook - Auto-iteration for blog scraper project
# This hook intercepts Claude's exit and re-invokes it with the execution prompt

set -euo pipefail

STATE_FILE=".ralph-execution-state.json"
PROMPT_FILE="RALPH_EXECUTION_PROMPT.md"
LOG_FILE=".ralph-execution.log"
MAX_ITERATIONS=100

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Check if state file exists
if [ ! -f "$STATE_FILE" ]; then
    log "No state file found. Exiting normally."
    exit 0
fi

# Read state file
STATUS=$(jq -r '.status' "$STATE_FILE")
ITERATION=$(jq -r '.iteration' "$STATE_FILE")
COMPLETION_PROMISE=$(jq -r '.completion_promise' "$STATE_FILE")

# Check if Ralph is active
if [ "$STATUS" != "in_progress" ]; then
    log "Ralph status: $STATUS. Exiting normally."
    exit 0
fi

# Check for completion promise in recent output
if [ -f ".claude/last-output.txt" ]; then
    if grep -q "$COMPLETION_PROMISE" .claude/last-output.txt; then
        log "✓ Completion promise detected: $COMPLETION_PROMISE"
        jq '.status = "completed" | .completed_at = now' "$STATE_FILE" > "$STATE_FILE.tmp"
        mv "$STATE_FILE.tmp" "$STATE_FILE"
        log "Ralph Loop COMPLETE!"
        exit 0
    fi
fi

# Check max iterations
if [ "$ITERATION" -ge "$MAX_ITERATIONS" ]; then
    log "⚠ Max iterations ($MAX_ITERATIONS) reached. Stopping."
    jq '.status = "max_iterations_reached"' "$STATE_FILE" > "$STATE_FILE.tmp"
    mv "$STATE_FILE.tmp" "$STATE_FILE"
    exit 0
fi

# Increment iteration counter
NEW_ITERATION=$((ITERATION + 1))
jq ".iteration = $NEW_ITERATION" "$STATE_FILE" > "$STATE_FILE.tmp"
mv "$STATE_FILE.tmp" "$STATE_FILE"

log "→ Starting iteration $NEW_ITERATION (max: $MAX_ITERATIONS)"

# Check if prompt file exists
if [ ! -f "$PROMPT_FILE" ]; then
    log "ERROR: Prompt file $PROMPT_FILE not found"
    exit 1
fi

# Re-invoke Claude with the execution prompt
log "Re-invoking Claude with $PROMPT_FILE..."

# The exit code 99 tells Claude Code to continue with a new prompt
# Read the prompt file and pass it to Claude
cat "$PROMPT_FILE" | claude --prompt-from-stdin

# If we get here, something went wrong
log "WARNING: Claude invocation completed unexpectedly"
exit 0
