# Ralph Execution Loop - Blog Post Scraper Implementation

You are Claude Code executing in a Ralph Loop to autonomously build the Blog Post Scraper project.

## Your Mission

Implement the blog post scraper by executing tasks sequentially from `HANDOFF_STAGES_PLAN.md`, one task per iteration.

## How Ralph Loop Works

1. **Read State**: Check `.ralph-execution-state.json` for current task
2. **Execute Task**: Implement the current task from HANDOFF_STAGES_PLAN.md
3. **Commit Work**: Git commit with descriptive message
4. **Update State**: Mark task complete, set next task
5. **Signal & Exit**: Output `<task-complete>X.Y</task-complete>` and STOP
6. **Hook Triggers**: Stop hook re-invokes you with this prompt (automatic)

**CRITICAL**: You MUST output `<task-complete>X.Y</task-complete>` before stopping so the hook can track progress.

## Current Iteration Instructions

### STEP 1: Read State File

```bash
cat .ralph-execution-state.json
```

Extract:
- `current_stage`: Which stage (1-6)
- `current_task`: Which task (e.g., "2.2")
- `current_task_description`: What to do
- `iteration`: Current iteration number

### STEP 2: Read Task Details from HANDOFF Plan

```bash
cat HANDOFF_STAGES_PLAN.md
```

Find the section for your current task (e.g., "Task 2.2: Data Models") and read:
- Checkboxes to complete
- Acceptance criteria
- Files to create
- What to implement

### STEP 3: Execute the Task

Follow the task checklist exactly:
- Create/modify files as specified
- Write clean, production-quality code
- Follow PRD requirements (read `PRD.md` if needed)
- Follow TECH_STACK decisions (read `TECH_STACK.md` if needed)
- Add proper error handling and logging
- Write docstrings for functions/classes

**Code Quality Standards:**
- Use type hints (Python 3.11+)
- Follow PEP 8 style
- Add structured logging (structlog)
- Handle errors gracefully
- Write self-documenting code

### STEP 4: Git Commit

After completing the task:

```bash
git add <files>
git commit -m "Task X.Y: <Brief description>

<Detailed description of what was implemented>
- Bullet point 1
- Bullet point 2

Stage X, Task X.Y complete."
```

### STEP 5: Update State File

Update `.ralph-execution-state.json`:

1. Mark current task as complete:
   - Add task to `stages[X].tasks_complete` array
   - Remove from `stages[X].tasks_pending` array

2. Set next task:
   - If more tasks in current stage: `current_task = "X.Y+1"`
   - If stage complete:
     - `stages[X].status = "completed"`
     - `current_stage = X+1`
     - `current_task = "X+1.1"`
   - Update `current_task_description`

3. Update notes:
   - `notes = "Task X.Y complete. Next: Task X.Y+1 - <description>"`

Example update:
```bash
jq '.stages["2"].tasks_complete += ["2.2"] |
    .stages["2"].tasks_pending = ["2.3"] |
    .current_task = "2.3" |
    .current_task_description = "Add Pydantic schemas with validation" |
    .notes = "Task 2.2 complete. Next: Task 2.3"' \
    .ralph-execution-state.json > .ralph-execution-state.json.tmp
mv .ralph-execution-state.json.tmp .ralph-execution-state.json
```

### STEP 6: Check for Completion

If ALL stages are complete:
- Update state: `"status": "completed"`
- Output the completion promise:

```
<promise>BLOG_SCRAPER_COMPLETE</promise>
```

This signals the hook to stop iterations.

### STEP 7: Signal Task Complete

Output the task completion signal:

```
<task-complete>X.Y</task-complete>
```

Replace X.Y with the actual task you just completed (e.g., `<task-complete>2.2</task-complete>`).

### STEP 8: STOP

**IMPORTANT**: After outputting the signal, STOP immediately. Do NOT continue to the next task.

The stop hook will:
- Detect `<task-complete>` signal
- Increment iteration counter
- Re-invoke you with this prompt
- You'll read the updated state and do the next task

## Special Cases

### If Tests Exist and Fail

If you create tests or run existing tests and they fail:
- Fix the failures in the SAME iteration
- Do NOT mark task complete until tests pass
- Iterate within the task until green

### If Blocked or Stuck

If you cannot complete a task:
1. Document the blocker in state file:
   ```json
   "blocker": {
     "task": "X.Y",
     "issue": "Description of what's blocking",
     "attempted": ["Thing 1", "Thing 2"],
     "needs": "What's needed to unblock"
   }
   ```
2. Output: `<blocked>Task X.Y blocked: <reason></blocked>`
3. STOP (hook will detect blocked status)

### If Max Iterations Reached

The hook will stop at 100 iterations. If you see:
- `iteration` near 100
- Many tasks remaining

Document what's incomplete and exit gracefully.

## Project Context

**Project**: Blog Post Scraper
**Tier**: STANDARD (MVP-level, no production features)
**Tech Stack**: Python 3.11, FastAPI, Playwright, SQLite, Bootstrap
**Git Branch**: feature/implementation (NEVER commit to main)

**Key Documents**:
- `PRD.md`: Product requirements and user stories
- `TECH_STACK.md`: Technology decisions and justifications
- `HANDOFF_STAGES_PLAN.md`: Task breakdown (98 checkboxes)

**Total Work**:
- 6 stages
- 98 tasks (checkboxes)
- Estimated: 12-16 hours

## Examples

### Example Iteration (Task 2.2)

```
1. Read state: current_task = "2.2"
2. Read HANDOFF: "Create BlogPost and ScrapingJob models"
3. Create src/models/blog_post.py (with UUID, indexes)
4. Create src/models/scraping_job.py (with status enum)
5. Create src/models/__init__.py (imports)
6. Git commit: "Task 2.2: Define database models"
7. Update state: current_task = "2.3", tasks_complete += ["2.2"]
8. Output: <task-complete>2.2</task-complete>
9. STOP
```

Hook re-invokes → You read state → current_task = "2.3" → Execute Task 2.3 → ...

## Debug Mode

If `LOG_LEVEL=DEBUG` in state:
- Log each step
- Show file contents after creation
- Explain decisions

## Ready to Start?

You are now in a Ralph Loop iteration. Follow the 8 steps above:

1. ✓ Read `.ralph-execution-state.json`
2. ✓ Read task from `HANDOFF_STAGES_PLAN.md`
3. ✓ Execute task (write code)
4. ✓ Git commit
5. ✓ Update state file
6. ✓ Check completion
7. ✓ Output `<task-complete>X.Y</task-complete>`
8. ✓ STOP

The stop hook will handle the rest. Let's build this scraper!

---

**Ralph Loop Version**: 1.0
**Max Iterations**: 100
**Completion Promise**: `BLOG_SCRAPER_COMPLETE`
**Status**: Active
