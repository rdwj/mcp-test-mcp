# Project Management Rules

**IMPORTANT**: These rules MUST be followed by all contributors, including AI assistants like Claude Code.

## Mandatory File Promotion Rules

### For AI Assistants (Claude Code)

You MUST use the promotion script at these specific points:

1. **Starting Work**
   - BEFORE working on any item in `backlog/`, you MUST run:
     ```bash
     ./project-management/scripts/promote.sh [filename] in-progress
     ```

2. **Encountering Blocks**
   - IMMEDIATELY when you discover you cannot proceed (missing dependency, external blocker, unclear requirements), you MUST run:
     ```bash
     ./project-management/scripts/promote.sh [filename] blocked
     ```
   - Add a note to the work item explaining the blocker

3. **Completing Work**
   - AFTER completing all work on an item in `in-progress/`, you MUST run:
     ```bash
     ./project-management/scripts/promote.sh [filename] ready-for-review
     ```
   - Do NOT consider the task complete until the file has been moved to `ready-for-review/`

4. **Returning from Blocked**
   - When you resume work on a blocked item, you MUST run:
     ```bash
     ./project-management/scripts/promote.sh [filename] in-progress
     ```

### For Human Reviewers

1. **Approving Work**
   - After reviewing and approving work in `ready-for-review/`, run:
     ```bash
     ./project-management/scripts/promote.sh [filename] done
     ```

2. **Requesting Changes**
   - If changes are needed, return the item to in-progress:
     ```bash
     ./project-management/scripts/promote.sh [filename] in-progress
     ```
   - Add comments to the work item describing what needs to change

## Workflow State Transitions

Valid transitions:

- `backlog` → `in-progress` (start work)
- `in-progress` → `blocked` (hit blocker)
- `in-progress` → `ready-for-review` (complete work)
- `blocked` → `in-progress` (unblocked, resume work)
- `ready-for-review` → `done` (approved)
- `ready-for-review` → `in-progress` (changes requested)

## YAML Frontmatter Requirements

Every work item MUST have YAML frontmatter with these fields:

```yaml
---
status: [current-status]
created_date: [ISO 8601 timestamp]
updated_date: [ISO 8601 timestamp]
history:
  - status: [previous-status]
    timestamp: [ISO 8601 timestamp]
  - status: [current-status]
    timestamp: [ISO 8601 timestamp]
---
```

The `promote.sh` script maintains these fields automatically.

## File Naming Convention

- Use: `YYYYMMDD-short-description.md` or `STORY-ID-description.md`
- Keep descriptions concise but meaningful
- Use lowercase with hyphens (kebab-case)

## Creating New Work Items

When creating a new work item:

1. Place it in `backlog/`
2. Use the proper naming convention
3. Include complete YAML frontmatter (status: backlog)
4. Include:
   - Description of the work
   - Acceptance criteria
   - Any relevant context or dependencies

## Blocked Items

When marking an item as blocked:

1. Move it to `blocked/` using the script
2. Add a "Blocker" section to the work item describing:
   - What is blocking progress
   - What is needed to unblock
   - Who/what can resolve the blocker
3. Do NOT leave items in `in-progress/` if you cannot proceed

## Review Process

Items in `ready-for-review/`:

- Must be complete according to acceptance criteria
- Should include notes on implementation decisions
- Must have all tests passing (if applicable)
- Should include any relevant documentation updates

## Critical Reminder for Claude Code

**DO NOT FORGET**: After you complete work on ANY task from `in-progress/`, you MUST promote it to `ready-for-review/` using the script. This is NOT optional. The human is relying on you to move files correctly.

If you are unsure whether work is complete, ask the human before promoting.
