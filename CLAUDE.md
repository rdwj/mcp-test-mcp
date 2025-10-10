# Project Management Workflow

This project uses a file-based project management system. **ALL work MUST follow this workflow.**

## Critical Rules for Claude Code

### Before Starting Any Work

1. Check `project-management/backlog/` for work items
2. When starting work on an item, you MUST run:
   ```bash
   ./project-management/scripts/promote.sh [filename] in-progress
   ```

### During Work

1. If you encounter a blocker, you MUST immediately run:
   ```bash
   ./project-management/scripts/promote.sh [filename] blocked
   ```
2. Add a note to the work item explaining what's blocking progress

### After Completing Work

1. When work is complete, you MUST run:
   ```bash
   ./project-management/scripts/promote.sh [filename] ready-for-review
   ```
2. **DO NOT consider a task complete until the file is in `ready-for-review/`**

### Workflow States

- `backlog/` - Identified work not yet started
- `in-progress/` - Currently working on
- `blocked/` - Cannot proceed due to dependencies or issues
- `ready-for-review/` - Complete, awaiting approval
- `done/` - Approved and completed

### State Transitions You Must Execute

- Starting work: `backlog` → `in-progress`
- Hit blocker: `in-progress` → `blocked`
- Complete work: `in-progress` → `ready-for-review`
- Unblocked: `blocked` → `in-progress`

### Finding Work Items

Before asking the user what to work on, check these locations:
1. `project-management/in-progress/` - Any items here need completion
2. `project-management/blocked/` - Check if you can now unblock any items
3. `project-management/backlog/` - New work to start

### Complete Documentation

Read `project-management/PROJECT-MANAGEMENT-RULES.md` for the full workflow specification.

## Reminder

**YOU MUST USE THE PROMOTION SCRIPT** at the appropriate points. The human is relying on you to manage file locations correctly. Forgetting to promote files breaks the workflow.
