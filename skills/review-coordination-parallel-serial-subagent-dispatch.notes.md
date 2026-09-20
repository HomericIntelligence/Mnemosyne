# Historical review-coordination examples

These prior prompts and thresholds document the captured session. They are not
current workflow requirements. Read them when reproducing the recorded grouping
or result format. Follow the main skill for current guidance.

## Verified Workflow

### Phase 1: Parse Review Threads

Read the PR review threads and extract:
- `thread_id`: GitHub comment ID
- `file`: path to file being reviewed
- `line`: line number (if applicable)
- `comment_text`: the review feedback
- `difficulty`: estimate (simple/medium/hard) based on:
  - Simple: data type change, off-by-one fix, variable rename (15 min, Haiku)
  - Medium: logic fix requiring test understanding, API change (45 min, Sonnet)
  - Hard: architectural change, deletion of large blocks, refactoring (2+ hours, Opus)

**Extraction Pattern**:
```bash
# Read PR review threads
gh pr view <pr-number> --json reviews

# Parse output to extract thread_id, file, line, comment_text, difficulty
# Group by file
```

### Phase 2: Group by File and Detect Serialization Requirement

**Grouping Rules**:
1. Group all threads by `file`
2. If a file has >1 thread:
   - Mark for **sequential dispatch** (same sub-agent or chained sub-agents)
   - Threads in same file must be fixed by the same agent in a single run to avoid edit race conditions
3. If each thread has a unique file:
   - Mark for **parallel dispatch** (different agents, independent execution)

**Result Structure**:
```json
{
  "sequential_groups": [
    {
      "file": "src/resnet18_impl.mojo",
      "threads": [
        {"thread_id": "c1", "line": 120, "difficulty": "simple"},
        {"thread_id": "c2", "line": 240, "difficulty": "hard"}
      ]
    }
  ],
  "parallel_groups": [
    {
      "file": "src/backward.mojo",
      "threads": [{"thread_id": "c3", "line": 50, "difficulty": "medium"}]
    }
  ]
}
```

### Phase 3: Route by Difficulty and Create Dispatch Plan

**Difficulty Tiers**:
- **Simple (Haiku)**: off-by-one, type change, variable rename, small logic fix (≤1 file, ≤50 lines)
- **Medium (Sonnet)**: logic fix, API change, feature addition (≤3 files, ≤200 lines)
- **Hard (Opus)**: architectural refactoring, deletion of major blocks (>3 files or >200 lines)

**Dispatch Rules**:
1. **Sequential groups**: Always dispatch to ONE agent (create a composite prompt with all threads for that file)
2. **Parallel groups**: Dispatch different files to different agents (by difficulty tier)
3. **Async execution**: Launch all agents in parallel (Bash `run_in_background: true`)
4. **Wait for all to complete**: Collect results before formatting/compiling

**Dispatch Prompt Template**:
```
You are fixing GitHub PR review comments. Your task:

1. Invoke /hephaestus:advise to search team knowledge for domain context on [DOMAIN]
2. Read the file(s) at [PATHS]
3. For each review thread below:
   - Thread #[THREAD_ID]: [COMMENT_TEXT]
   - Apply the fix on line [LINE]
   - Verify the fix makes sense in context
4. Reply with:
   - thread_id: [THREAD_ID]
   - summary: [ONE-LINER: what you fixed]
   - verification: [BRIEF CONFIRM IT COMPILES/PASSES TEST]
```

### Phase 4: Invoke Sub-Agents

**For Sequential Groups** (same file):
```bash
# Create ONE agent dispatch with all threads for this file
# Prompt includes: /hephaestus:advise + all threads in one call
Agent(
  description: "Fix [N] review comments in [filename]",
  prompt: "Domain: [context]. Threads: [all thread IDs for this file]. ...",
  run_in_background: true
)
```

**For Parallel Groups** (different files):
```bash
# Create N independent agent dispatches
Agent(description: "Fix review comment [thread_id] in [filename]", ...)  # Haiku/simple
Agent(description: "Fix review comment [thread_id] in [filename]", ...)  # Sonnet/medium
Agent(description: "Fix review comment [thread_id] in [filename]", ...)  # Opus/hard
# All run in parallel
```

### Phase 5: Aggregate Results

After all agents complete, collect results in a table:

| Thread ID | File | Summary | Verification | Status |
|-----------|------|---------|--------------|--------|
| c1 | backward.mojo | Changed `fwd.gap` → `fwd.s4b2_cache.block_out` for correct gradient shape | Compiles ✓ | Fixed |
| c2 | backward.mojo | Changed `fwd.relu1_out` → `fwd.bn1_pre_relu` for correct ReLU mask | Compiles ✓ | Fixed |
| c3 | train.mojo | Changed integer labels `(4,)` → one-hot labels `(4, 10)` for cross_entropy | Tests pass ✓ | Fixed |
| c4 | backward.mojo | Deleted 48-line BN stats revert block that froze running mean/var | Compiles ✓ | Fixed |

### Phase 6: Verify, Format, and Commit

1. **Verify compilation**: `pixi run mojo build` or `just build`
2. **Verify formatting**: `mojo format --check` (should be clean)
3. **Verify tests**: If applicable, run relevant test suite
4. **Commit**:
   ```bash
   git add <files>
   git commit -m "$(cat <<'EOF'
   fix(module): Address [N] critical review comments

   - Thread c1: [fix summary]
   - Thread c2: [fix summary]
   - Thread c3: [fix summary]
   - Thread c4: [fix summary]

   All fixes verified to compile with --Werror.

   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"
   ```

## Results & Parameters

### Model Tier Thresholds

```json
{
  "haiku": {
    "max_files": 1,
    "max_lines": 50,
    "max_threads": 1,
    "examples": ["variable rename", "type fix", "off-by-one", "import reorder"]
  },
  "sonnet": {
    "max_files": 3,
    "max_lines": 200,
    "max_threads": 2,
    "examples": ["API change", "logic fix with tests", "feature addition"]
  },
  "opus": {
    "max_files": "unlimited",
    "max_lines": "unlimited",
    "max_threads": "unlimited",
    "examples": ["architectural refactor", "major deletion", ">200 line rewrites"]
  }
}
```

### Thread Aggregation Format

Each sub-agent returns:
```json
{
  "thread_id": "c1",
  "file": "backward.mojo",
  "summary": "Changed `fwd.gap` → `fwd.s4b2_cache.block_out` for correct gradient dimensions",
  "verification": "Compiles with mojo build --Werror",
  "status": "fixed"
}
```

Orchestrator aggregates all into:
```json
{
  "fixed_threads": [
    {"thread_id": "c1", "file": "backward.mojo", "summary": "..."},
    {"thread_id": "c2", "file": "backward.mojo", "summary": "..."},
    {"thread_id": "c3", "file": "impl.mojo", "summary": "..."},
    {"thread_id": "c4", "file": "backward.mojo", "summary": "..."}
  ],
  "verification": {
    "compilation": "All fixes verified with mojo build --Werror",
    "formatting": "Code clean (mojo format)",
    "tests": "All tests passing"
  },
  "commit": "cb3deb5c"
}
```

## Key Insights

1. **File Grouping First**: Always group review threads by file before dispatching agents. Same-file threads must be handled by the same agent in one prompt to avoid edit races.

2. **Parallel When Safe**: Different files → different agents in parallel (speed up). Same file → same agent sequentially (correctness).

3. **Model Tier by Difficulty**: Simple fixes (Haiku) vs. medium logic (Sonnet) vs. hard refactoring (Opus). Mismatched tiers waste tokens or produce incorrect code.

4. **Domain Knowledge**: Every sub-agent's first instruction must be `/hephaestus:advise [domain]` to ground context before applying fixes.

5. **Aggregation Before Commit**: Collect all results in a single table, verify compilation/tests, then create one atomic commit.

6. **One-Liner Summaries**: Thread_id + one-liner enables quick spot-checking of what was fixed and why.

