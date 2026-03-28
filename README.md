# Voting System

## Fix for "Binary files are not supported" during PR creation

Some PR creation tools fail when a commit contains raw binary blobs. This repository now includes a `.gitattributes` file that routes common binary extensions through Git LFS so commits store text-based pointer files instead of embedding raw binary data in normal Git objects.

### One-time setup

```bash
git lfs install
```

### Re-add existing binary files (if already committed)

```bash
git rm --cached path/to/file.png
git add path/to/file.png
git commit -m "Track binary with LFS"
```

### Verify

```bash
git lfs ls-files
```

If your PR tool still errors, ensure the changed files match extensions listed in `.gitattributes` or add additional patterns as needed.
