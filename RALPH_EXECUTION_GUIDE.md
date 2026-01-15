# Ralph Loop Execution Guide

## What We Built

A custom Stop hook system that enables auto-run Ralph Loop execution for the blog scraper project.

## Files Created

1. **`.claude/hooks/stop-hook.sh`** - Intercepts Claude exit and triggers next iteration
2. **`RALPH_EXECUTION_PROMPT.md`** - Instructions fed to Claude in each iteration
3. **`.ralph-execution-state.json`** - Tracks current task, stage, and progress (gitignored)

## How It Works

```
┌─────────────────────────────────────────┐
│  Claude reads state: current_task=2.2   │
│  Executes Task 2.2 from HANDOFF plan    │
│  Creates models, commits to git         │
│  Updates state: current_task=2.3        │
│  Outputs: <task-complete>2.2</task>     │
│  Tries to exit...                       │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  Stop Hook (.claude/hooks/stop-hook.sh) │
│  - Reads .ralph-execution-state.json    │
│  - Status = in_progress? Continue!      │
│  - Re-invokes Claude with prompt        │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  Fresh Claude context (auto-triggered)  │
│  Reads state: current_task=2.3          │
│  Executes Task 2.3...                   │
│  Loop continues automatically           │
└─────────────────────────────────────────┘
```

## How to Test

### Option 1: Manual Trigger (Simpler Test)

From the test-blog-scraper directory, just send a message with the prompt:

```
Please follow the instructions in RALPH_EXECUTION_PROMPT.md to execute the current task.
```

I'll execute one task, update state, output `<task-complete>`, and exit. Then you can send the same message again to trigger the next iteration.

### Option 2: Auto-Run via Stop Hook

If Claude Code supports stop hooks (this is the goal):

```bash
cd /home/bartek/test-blog-scraper

# Initialize state is already done
# Just send this message to Claude:
"Execute RALPH_EXECUTION_PROMPT.md. When you exit, the stop hook will auto-trigger the next iteration."
```

If the hook works, Claude will:
1. Execute Task 2.2
2. Try to exit
3. Hook catches and re-invokes automatically
4. Continue until all 98 tasks done OR 100 iterations reached

### Option 3: Use Official Plugin (Fallback)

If our custom hook doesn't work, use the official ralph-loop plugin:

```bash
cd /home/bartek/test-blog-scraper

# Run with official plugin
/ralph-loop "$(cat RALPH_EXECUTION_PROMPT.md)" \
  --completion-promise "BLOG_SCRAPER_COMPLETE" \
  --max-iterations 100
```

## Current State

```json
{
  "current_stage": 2,
  "current_task": "2.2",
  "current_task_description": "Create BlogPost and ScrapingJob models",
  "iteration": 0,
  "status": "in_progress"
}
```

**Tasks Complete**: 1.1, 1.2, 1.3, 2.1 (4 of 98)
**Tasks Remaining**: 94
**Next Task**: Task 2.2 - Define database models

## Monitoring Progress

### Check Current State
```bash
cat .ralph-execution-state.json | jq '.current_task, .iteration'
```

### View Logs
```bash
tail -f .ralph-execution.log
```

### Check Git History
```bash
git log --oneline feature/implementation
```

Each task should have a descriptive commit message like:
```
Task 2.2: Define database models
Task 2.3: Add Pydantic schemas with validation
Task 3.1: Implement URL validator (SEC-01)
...
```

## Stopping the Loop

### Graceful Stop
The loop will automatically stop when:
- All tasks complete (outputs `<promise>BLOG_SCRAPER_COMPLETE</promise>`)
- Max iterations reached (100)
- Status changes to anything other than "in_progress"

### Manual Stop
Update the state file:
```bash
jq '.status = "paused"' .ralph-execution-state.json > .ralph-execution-state.json.tmp
mv .ralph-execution-state.json.tmp .ralph-execution-state.json
```

### Emergency Stop
If the hook is running wild:
1. Kill the Claude process
2. Delete or rename `.claude/hooks/stop-hook.sh`
3. Fix the issue
4. Resume by restoring the hook

## Expected Output

When working correctly, you should see:
```
→ Starting iteration 1 (max: 100)
Re-invoking Claude with RALPH_EXECUTION_PROMPT.md...

[Claude executes Task 2.2]
<task-complete>2.2</task-complete>

→ Starting iteration 2 (max: 100)
Re-invoking Claude with RALPH_EXECUTION_PROMPT.md...

[Claude executes Task 2.3]
<task-complete>2.3</task-complete>

...

✓ Completion promise detected: BLOG_SCRAPER_COMPLETE
Ralph Loop COMPLETE!
```

## Troubleshooting

### Hook Not Triggering
- Check if `.claude/hooks/stop-hook.sh` is executable: `ls -l .claude/hooks/`
- Check if Claude Code supports stop hooks (may be version-specific)
- Fallback: Use manual trigger or official plugin

### State File Not Updating
- Check file permissions: `ls -l .ralph-execution-state.json`
- Verify jq is installed: `jq --version`
- Check logs: `tail -20 .ralph-execution.log`

### Claude Stuck in Loop
- Check iteration count: `jq '.iteration' .ralph-execution-state.json`
- Look for blockers: `jq '.blocker' .ralph-execution-state.json`
- Review recent git commits: `git log --oneline -10`

### Tests Failing
Claude should fix test failures within the same iteration. If tests keep failing:
- Check test output in logs
- Manually review the test
- Fix if bug in test itself
- Update state to skip that task temporarily

## Success Criteria

Ralph Loop is successful when:
- ✅ All 6 stages completed
- ✅ All 98 tasks checked off in HANDOFF_STAGES_PLAN.md
- ✅ All tests passing (`pytest`)
- ✅ Docker build succeeds
- ✅ All 6 user stories verified (PRD.md)
- ✅ State file shows: `"status": "completed"`

## Next Steps After Completion

1. Review all commits: `git log feature/implementation`
2. Run final tests: `pytest --cov=src`
3. Build Docker image: `docker build -t blog-scraper:latest .`
4. Test end-to-end: Run the application and test all user stories
5. Merge to main: `git checkout main && git merge feature/implementation`
6. Create release: Tag the final version

---

**Ready to test?** Just send me a message to trigger the first iteration!
