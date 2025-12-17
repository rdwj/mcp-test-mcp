# Release to npm

Publish a new version of mcp-test-mcp to npm.

## Usage

```
/release <version>
```

Example: `/release 0.2.1`

## Process

### Step 1: Validate Version

1. Parse the version from the command argument (e.g., `0.2.1`)
2. Verify it follows semver format (X.Y.Z)
3. Check that the new version is greater than the current version in `node-wrapper/package.json`

If no version is provided, ask the user what version they want to release.

### Step 2: Run Pre-Release Checks

Run security scan:
```bash
gitleaks detect --source . --verbose
```

If secrets are found, STOP and report. Do not proceed.

### Step 3: Check Git Status

```bash
git status --porcelain
```

If there are uncommitted changes, ask the user:
- Include them in the release commit?
- Or abort and let them handle it first?

### Step 4: Update Version Numbers

Update version in both files:
- `pyproject.toml`: Update `version = "X.Y.Z"`
- `node-wrapper/package.json`: Update `"version": "X.Y.Z"`

### Step 5: Sync README

Copy the main README to the npm package:
```bash
cp README.md node-wrapper/README.md
```

### Step 6: Stage and Commit

```bash
git add pyproject.toml node-wrapper/package.json node-wrapper/README.md
```

If user chose to include other changes in Step 3:
```bash
git add .
```

Create commit:
```bash
git commit -m "$(cat <<'EOF'
chore: Release vX.Y.Z

<brief description of changes since last release if available>

Assisted-by: Claude Code (Opus 4.5)
EOF
)"
```

### Step 7: Push to Main

```bash
git push origin main
```

### Step 8: Create and Push Tag

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

### Step 9: Monitor Workflow

Check the GitHub Actions workflow:
```bash
gh run list --limit 1
```

Wait for completion (poll every 5 seconds, max 60 seconds):
```bash
gh run view <run-id> --json status,conclusion
```

### Step 10: Verify Publication

Once workflow succeeds:
```bash
npm view mcp-test-mcp version
```

Confirm the new version is live.

## Summary Report

After completion, provide:

```
Release Complete

Version: X.Y.Z
Tag: vX.Y.Z
npm: https://www.npmjs.com/package/mcp-test-mcp

Workflow: <success/failure>
Published: <timestamp>
```

## Error Handling

### Version Already Exists
```
Error: Tag vX.Y.Z already exists.
Please choose a different version number.
```

### Workflow Fails
```
Workflow failed. Check the logs:
gh run view <run-id> --log-failed

You may need to:
1. Fix the issue
2. Delete the tag: git tag -d vX.Y.Z && git push origin :refs/tags/vX.Y.Z
3. Try again with /release X.Y.Z
```

### npm Verification Fails
```
Warning: npm shows version X.Y.Z but expected A.B.C
Check https://www.npmjs.com/package/mcp-test-mcp manually.
npm registry may have propagation delay.
```
