# Project Management Workflow

This directory contains a file-based project management system for tracking work items through their lifecycle.

## Directory Structure

- **backlog/**: Work items that have been identified but not yet started
- **in-progress/**: Work items currently being worked on
- **ready-for-review/**: Completed work awaiting review and approval
- **done/**: Completed and approved work items
- **blocked/**: Work items that are blocked by dependencies or issues

## Workflow

Work items flow through these states:

```
backlog → in-progress → ready-for-review → done
              ↓              ↓
           blocked    →  in-progress (rework)
```

## Using the Promotion Script

Use the `scripts/promote.sh` script to move items between directories:

```bash
# Start working on a backlog item
./scripts/promote.sh STORY-123.md in-progress

# Mark as blocked
./scripts/promote.sh STORY-123.md blocked

# Complete work and request review
./scripts/promote.sh STORY-123.md ready-for-review

# Move to done after approval
./scripts/promote.sh STORY-123.md done

# Return to in-progress if changes needed
./scripts/promote.sh STORY-123.md in-progress
```

The script automatically updates the YAML frontmatter in each file to track status and history.

## File Naming Convention

Work items should follow this naming pattern:
- `YYYYMMDD-short-description.md` (e.g., `20250929-implement-auth.md`)
- Or: `STORY-ID-short-description.md` (e.g., `STORY-123-user-login.md`)

## Work Item Template

Each work item should include YAML frontmatter:

```yaml
---
status: backlog
created_date: 2025-09-29T10:30:00Z
updated_date: 2025-09-29T10:30:00Z
history:
  - status: backlog
    timestamp: 2025-09-29T10:30:00Z
---

# Title of Work Item

## Description
[What needs to be done]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Notes
[Any additional context]
```

## Important

**All contributors (human and AI) MUST read and follow the rules in `PROJECT-MANAGEMENT-RULES.md`.**
