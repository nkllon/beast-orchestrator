# AGENT.md - Maintainer Guide for AI Agents

**Repository:** beast-orchestrator  
**Current Maintainer:** AI Agent (You)  
**Last Updated:** 2025-10-14  
**Project Status:** Under Development (Alpha)

---

## 🎯 Welcome, AI Maintainer!

You are the primary maintainer of **Beast Orchestrator**, the coordination layer for Beast Mode clusters. This project orchestrates and coordinates work across multiple LLM nodes, managing task assignment, load balancing, and workflow execution. This project is being **100% implemented by LLMs using spec-driven development**.

## 🚧 Current Status: Scaffold Phase

This repository was just created from the beast-mailbox-core template using SPEC-002 (Repository Scaffold Procedure). The structure is in place, but **implementation has not started yet**.

**What exists:**
- ✅ Project structure (src/, tests/, docs/, .spec-workflow/)
- ✅ Build configuration (pyproject.toml)
- ✅ CI/CD workflows (GitHub Actions, SonarCloud)
- ✅ Quality tooling setup
- ✅ This maintainer guide

**What needs to be built:**
- ❌ Task scheduler and queue
- ❌ Node discovery and health monitoring
- ❌ Load balancing algorithm
- ❌ Workflow coordination
- ❌ Failover handling
- ❌ Tests
- ❌ Documentation

**Where to start:**
1. Create specifications in `.spec-workflow/specs/`
2. Follow spec-driven development pattern
3. Implement based on requirements
4. Write tests first (TDD)
5. Maintain quality standards

---

## Project Overview

### What is Beast Orchestrator?

The **coordination layer** for Beast Mode clusters that:
- Assigns tasks to appropriate LLM nodes based on capabilities
- Manages task queues and priorities
- Monitors node health and capacity
- Coordinates multi-step workflows
- Handles failover and load balancing

### Architecture Vision

```
┌─────────────────────────────────────────────────┐
│          Beast Orchestrator                      │
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │  Task Scheduler                           │  │
│  │  - Priority queue                         │  │
│  │  - Node selection algorithm               │  │
│  │  - Retry logic                            │  │
│  └────────────┬──────────────────────────────┘  │
│               │                                  │
└───────────────┼──────────────────────────────────┘
                │
                ▼
    ┌───────────────────────────┐
    │   Redis Mailbox           │
    │   (beast-mailbox-core)    │
    └───────────┬───────────────┘
                │
    ┌───────────┴───────────┐
    │                       │
    ▼                       ▼
┌─────────┐            ┌─────────┐
│ Node 1  │            │ Node 2  │
│ (LLM)   │            │ (LLM)   │
└─────────┘            └─────────┘
```

### Key Responsibilities

1. **Task Scheduling** - Assign tasks to appropriate nodes
2. **Load Balancing** - Distribute work based on capacity
3. **Health Monitoring** - Track node availability
4. **Workflow Coordination** - Multi-step task execution
5. **Failover** - Handle node failures gracefully

[Keep remaining sections from AGENT.md template, updating references]

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Design](#architecture--design)
3. [Quality Standards](#quality-standards)
4. [Development Workflow](#development-workflow)
5. [Testing Requirements](#testing-requirements)
6. [Release Procedure](#release-procedure)
7. [Common Maintenance Tasks](#common-maintenance-tasks)
8. [Tools & Integrations](#tools--integrations)
9. [Critical Lessons from History](#critical-lessons-from-history)
10. [Troubleshooting Guide](#troubleshooting-guide)
11. [Quick Reference](#quick-reference)

---

## Project Overview

### What is Beast Mailbox Core?

A Python package providing **Redis Streams-based mailbox utilities** for inter-agent communication. Think of it as a message bus for AI agents to communicate with each other reliably.

**Core Features:**
- Durable messaging via Redis Streams (`XADD`/`XREADGROUP`)
- Consumer groups per agent ID (at-least-once delivery)
- Async handler registration for inbound messages
- CLI tools: `beast-mailbox-service` and `beast-mailbox-send`
- One-shot message inspection with optional ack/trim operations

**Current Version:** 0.3.1  
**Python Support:** 3.9, 3.10, 3.11, 3.12  
**Package:** [pypi.org/project/beast-mailbox-core](https://pypi.org/project/beast-mailbox-core/)

### Key Files Structure

```
beast-mailbox-core/
├── src/beast_mailbox_core/
│   ├── __init__.py           # Public API exports
│   ├── redis_mailbox.py      # Core service (MailboxMessage, RedisMailboxService)
│   └── cli.py                # CLI entry points
├── tests/                    # 59 tests, 90% coverage
│   ├── test_redis_mailbox.py
│   ├── test_cli_functions.py
│   └── [7 more test files]
├── docs/
│   ├── LESSONS_LEARNED_v0.3.0.md  # CRITICAL: Read this for context
│   ├── QUICK_REFERENCE.md
│   └── USAGE_GUIDE.md
├── steering/
│   └── release-procedure-CORRECTED.md  # MANDATORY release process
├── pyproject.toml            # Package metadata, pytest config
├── sonar-project.properties  # SonarCloud configuration
└── README.md                 # User-facing documentation
```

---

## Architecture & Design

### Core Components

#### 1. **MailboxMessage** (Data Model)
```python
@dataclass
class MailboxMessage:
    message_id: str
    sender: str
    recipient: str
    payload: Dict[str, Any]
    message_type: str = "direct_message"
    timestamp: float
```

Serializes to/from Redis using `to_redis_fields()` and `from_redis_fields()`.

#### 2. **RedisMailboxService** (Core Service)
```python
class RedisMailboxService:
    - connect() / disconnect()          # Redis lifecycle
    - start() / stop()                  # Service lifecycle
    - register_handler(callable)        # Async message handlers
    - send_message(recipient, payload)  # Send to other agents
    - _consume_loop()                   # Infinite consumer loop (intentionally untestable)
```

**Design Pattern:** Async service with background task for message consumption.

#### 3. **CLI Tools** (User Interface)
- `beast-mailbox-service <agent_id>` - Start listener or inspect messages
- `beast-mailbox-send <sender> <recipient>` - Send messages

**Key CLI Functions:**
- `_fetch_latest_messages()` - One-shot inspection (supports `--ack`, `--trim`)
- `run_service_async()` - Long-running service mode
- `_acknowledge_messages()` / `_trim_messages()` - Helper functions (extracted for complexity)

### Redis Streams Architecture

**Stream Naming:** `beast:mailbox:<agent_id>:in`

Example: Agent "alice" receives messages on stream `beast:mailbox:alice:in`

**Consumer Groups:** `<agent_id>:group`

**Pattern:**
```python
# Send
await client.xadd("beast:mailbox:bob:in", fields, maxlen=1000)

# Receive
response = await client.xreadgroup(
    groupname="bob:group",
    consumername="bob-consumer",
    streams={"beast:mailbox:bob:in": ">"},
    count=10,
    block=2000
)
```

### Intentionally Untestable Code

Two infinite event loops are **architecturally untestable** in unit tests:
1. `cli.py` lines 200-242: `run_service_async()` event loop
2. `redis_mailbox.py` lines 316-343: `_consume_loop()` infinite loop

**Current Coverage:** 90% (100% of testable code)

**Decision:** Accept this. Don't compromise architecture for metrics. Use integration tests instead.

---

## Quality Standards

### Current Quality Metrics (v0.3.1)

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Tests** | ≥ Cognitive Complexity | 59 (125% of 47) | ✅ EXCELLENT |
| **Coverage** | ≥ 80% | 90% | ✅ EXCELLENT |
| **Comment Density** | ≥ 25% | 52.2% | ✅ EXCEPTIONAL |
| **Bugs** | 0 | 0 | ✅ PERFECT |
| **Code Smells** | 0 | 0 | ✅ PERFECT |
| **Quality Gate** | PASSED | PASSED | ✅ |
| **Maintainability** | A | A | ✅ |
| **Reliability** | A | A | ✅ |
| **Security** | A | A | ✅ |

### Non-Negotiable Standards

1. **Zero Defects:** No bugs, vulnerabilities, or critical code smells
2. **High Coverage:** Maintain ≥ 85% code coverage
3. **Documentation Density:** Keep ≥ 40% comment density
4. **Tests ≥ Complexity:** Number of tests should exceed cognitive complexity
5. **Quality Gate:** Must pass SonarCloud Quality Gate before release
6. **All Tests Pass:** 100% test success rate

### Documentation Standards

**Every function/class must have:**
- One-line summary
- Detailed description (what, why, how)
- Args section with type and usage
- Returns section
- Raises section (if applicable)
- Example section (when helpful)
- Note section (for design decisions, gotchas)

**Format:**
```python
def function_name(param: Type) -> ReturnType:
    """One-line summary.
    
    Detailed description explaining the purpose, behavior,
    and important context. Include design decisions.
    
    Args:
        param: Description including constraints
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When and why
        
    Example:
        >>> result = function_name("value")
        >>> print(result)
        
    Note:
        Design decisions, warnings, or related functions
    """
```

---

## Development Workflow

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/nkllon/beast-mailbox-core.git
cd beast-mailbox-core

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
pytest tests/
beast-mailbox-service --help
```

### Making Changes

1. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write code with tests:**
   - Write/modify code in `src/beast_mailbox_core/`
   - Add corresponding tests in `tests/`
   - Add comprehensive docstrings

3. **Run tests locally:**
   ```bash
   pytest tests/ --cov=src/beast_mailbox_core --cov-report=term-missing
   ```

4. **Check coverage:**
   - Overall: Must be ≥ 85%
   - New code: Must be ≥ 80%

5. **Commit with conventional commits:**
   ```bash
   git commit -m "feat: add new feature"
   git commit -m "fix: resolve bug in handler"
   git commit -m "docs: update docstrings"
   git commit -m "test: add edge case tests"
   git commit -m "chore: bump dependencies"
   ```

6. **Push and verify CI:**
   ```bash
   git push origin feature/your-feature-name
   ```
   
   GitHub Actions will:
   - Run all tests
   - Generate coverage report
   - Run SonarCloud scan
   - Report Quality Gate status

---

## Testing Requirements

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_mailbox_config.py   # Config tests
├── test_mailbox_message.py  # Message serialization tests
├── test_mailbox_service.py  # High-level API tests
├── test_redis_mailbox.py    # Core service tests (16 tests)
├── test_cli_functions.py    # CLI function tests
├── test_cli_helpers.py      # CLI helper tests
├── test_edge_cases.py       # Edge cases & integration
└── test_coverage_boost.py   # Additional coverage tests
```

### Testing AsyncIO Code

**Key Patterns:**

```python
# 1. Use AsyncMock for Redis clients
from unittest.mock import AsyncMock, patch

mock_client = AsyncMock()
mock_client.xadd = AsyncMock(return_value=b"123-0")

with patch('beast_mailbox_core.redis_mailbox.redis.Redis', return_value=mock_client):
    result = await service.send_message("bob", {"msg": "hi"})
```

```python
# 2. Test lifecycle with real tasks
async def test_start_stop():
    service = RedisMailboxService("test", config)
    await service.start()  # Creates background task
    assert service._processing_task is not None
    await service.stop()   # Cancels task gracefully
    assert service._processing_task is None
```

```python
# 3. Test cancellation with real tasks
async def test_cancellation():
    # Create real task (not AsyncMock - those can't be awaited properly)
    async def dummy():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            pass
    
    service._processing_task = asyncio.create_task(dummy())
    await service.stop()  # Should cancel without errors
```

### Running Tests

```bash
# All tests
pytest tests/

# With coverage
pytest tests/ --cov=src/beast_mailbox_core --cov-report=term-missing

# Specific file
pytest tests/test_redis_mailbox.py -v

# Specific test
pytest tests/test_cli_functions.py::TestFetchLatestMessages::test_ack_flag -v

# With verbose async debugging
pytest tests/ -v --log-cli-level=DEBUG
```

### Coverage Targets

- **Overall:** ≥ 85% (currently 90%)
- **New Code:** ≥ 80%
- **Testable Code:** 100%

**Acceptable Untested:**
- Infinite event loops (`while True` / `while self._running`)
- Integration scenarios requiring real Redis

---

## Release Procedure

> ⚠️ **CRITICAL:** Read `steering/release-procedure-CORRECTED.md` before any release.

### Historical Context

**v0.2.0 Crisis:** A release was published to PyPI without committing to the repository, causing a critical repository sync failure. This **must never happen again**.

### Mandatory Release Checklist

#### Pre-Release

1. ✅ All changes committed and pushed to GitHub
2. ✅ All tests pass locally (`pytest tests/`)
3. ✅ Coverage ≥ 85% (`pytest --cov`)
4. ✅ Quality Gate PASSED on SonarCloud
5. ✅ No linter errors
6. ✅ CHANGELOG.md updated with release notes
7. ✅ Version bumped in `pyproject.toml`

#### Release Steps

```bash
# 1. Create release branch
git checkout -b release/v0.X.Y

# 2. Update version and changelog
# Edit pyproject.toml: version = "0.X.Y"
# Edit CHANGELOG.md: Add [0.X.Y] section

git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.X.Y"
git push origin release/v0.X.Y

# 3. Create PR, get review, merge to main

# 4. Pull merged changes and tag
git checkout main
git pull origin main
git tag -a v0.X.Y -m "Release version 0.X.Y"
git push origin v0.X.Y

# 5. Verify tag exists
git ls-remote --tags origin | grep v0.X.Y

# 6. Build package
rm -rf dist/ build/ *.egg-info
python -m build

# 7. Upload to PyPI
twine upload dist/*

# 8. Verify on PyPI
pip install beast-mailbox-core==0.X.Y
pip show beast-mailbox-core

# 9. Create GitHub Release
gh release create v0.X.Y \
  --title "v0.X.Y" \
  --notes "$(cat CHANGELOG.md | sed -n '/\[0.X.Y\]/,/\[0/p' | head -n -1)"
```

### Release Rules (Never Break These)

❌ **NEVER:**
1. Publish without pushing commits first
2. Publish without creating a git tag
3. Skip code review (even for version bumps)
4. Rush a release
5. Publish from wrong directory
6. Skip Test PyPI (for major changes)

✅ **ALWAYS:**
1. Follow the checklist completely
2. Verify tag is pushed before publishing
3. Update CHANGELOG.md with accurate information
4. Create GitHub Release after publishing
5. Verify on PyPI after upload

---

## Common Maintenance Tasks

### Adding a New Feature

1. **Plan the feature:**
   - How does it fit the architecture?
   - What's the API design?
   - What are the test cases?

2. **Implement with TDD:**
   ```bash
   # Write failing test first
   vim tests/test_new_feature.py
   pytest tests/test_new_feature.py  # Should fail
   
   # Implement feature
   vim src/beast_mailbox_core/redis_mailbox.py
   pytest tests/test_new_feature.py  # Should pass
   ```

3. **Add comprehensive documentation:**
   - Module-level docstring (if new file)
   - Class docstring with examples
   - Function docstrings (Args/Returns/Raises/Example)

4. **Verify quality:**
   ```bash
   pytest tests/ --cov
   # Check coverage ≥ 85%
   
   git push origin feature/your-feature
   # Wait for SonarCloud scan
   ```

### Fixing a Bug

1. **Reproduce the bug:**
   - Create a failing test case
   - Verify it fails

2. **Fix the bug:**
   - Implement minimal fix
   - Verify test passes
   - Check for regressions

3. **Document the fix:**
   - Update CHANGELOG.md under `### Fixed`
   - Add inline comments if design decision changed
   - Reference issue number if applicable

### Updating Dependencies

```bash
# Check for updates
pip list --outdated

# Update specific dependency
# Edit pyproject.toml
vim pyproject.toml

# Test with new version
pip install -e ".[dev]"
pytest tests/

# Verify no breaking changes
```

**Dependabot:** Automatically creates PRs for dependency updates. Review and merge if tests pass.

### Improving Documentation

**Where to document:**
- `README.md` - User-facing usage guide
- `docs/USAGE_GUIDE.md` - Detailed usage patterns
- `docs/QUICK_REFERENCE.md` - Command cheat sheet
- Docstrings - API documentation
- `AGENT.md` (this file) - Maintainer guidance

**When to update:**
- After adding features (update README, docstrings)
- After fixing bugs (update troubleshooting sections)
- After learning lessons (update AGENT.md)

### Handling Issues and PRs

**Issues:**
1. Acknowledge quickly (within 24 hours)
2. Reproduce the issue
3. Create test case
4. Fix and verify
5. Release if critical

**Pull Requests:**
1. Review code quality
2. Check test coverage
3. Verify CI passes (GitHub Actions + SonarCloud)
4. Request changes if needed
5. Merge when quality standards met

---

## Tools & Integrations

### GitHub Actions

**Workflow:** `.github/workflows/sonarcloud.yml`

**Triggers:**
- Push to main
- Pull requests

**Steps:**
1. Checkout code
2. Set up Python 3.12
3. Install dependencies
4. Run pytest with coverage
5. Generate `coverage.xml`
6. Run SonarCloud scan
7. Report Quality Gate status

**Secrets Required:**
- `SONAR_TOKEN` - SonarCloud authentication

### SonarCloud

**Project:** `nkllon_beast-mailbox-core`  
**Organization:** `nkllon`  
**URL:** https://sonarcloud.io/project/overview?id=nkllon_beast-mailbox-core

**Configuration:** `sonar-project.properties`

**Key Settings:**
```properties
sonar.projectKey=nkllon_beast-mailbox-core
sonar.organization=nkllon
sonar.sources=src
sonar.tests=tests
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.version=3.9,3.10,3.11,3.12
sonar.exclusions=**/docs/**,**/prompts/**,**/__pycache__/**
```

**Quality Gate Conditions:**
- New reliability rating ≤ A
- New security rating ≤ A
- New maintainability rating ≤ A
- New coverage ≥ 80%
- New duplicated lines density ≤ 3%

**Important:** New code period is 30 days. Focus on keeping new code high quality.

**Critical:** Use the correct GitHub Action for SonarCloud:
```yaml
- name: SonarCloud Scan
  uses: SonarSource/sonarcloud-github-action@master  # ✅ Correct for SonarCloud
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

❌ **WRONG:** `SonarSource/sonarqube-scan-action` - This is for self-hosted SonarQube Server, NOT SonarCloud. Using the wrong action will cause authentication failures.

**Setting up SONAR_TOKEN:**
```bash
# Generate token at https://sonarcloud.io/account/security
# Set it as GitHub secret:
gh secret set SONAR_TOKEN --body "your-token-here" --repo nkllon/beast-mailbox-core

# Verify it's set:
gh secret list --repo nkllon/beast-mailbox-core
```

### GitHub Tokens & gh CLI

**Token Types:**

GitHub offers two types of Personal Access Tokens:

1. **Classic Tokens** (`ghp_...`) - **Recommended for CLI automation**
   - Work immediately on all repos you have access to
   - Simple scope-based permissions (check "repo" for full access)
   - No per-repository or organization approval needed
   - Generate at: https://github.com/settings/tokens/new

2. **Fine-Grained Tokens** (`github_pat_...`) - More secure but complex
   - Require explicit per-repository access configuration
   - For organization repos: May require organization admin approval
   - Better security isolation but more setup required
   - Generate at: https://github.com/settings/personal-access-tokens/new

**For Organization Repos (like nkllon/beast-mailbox-core):**

Classic tokens "just work". Fine-grained tokens require:
- Explicit repository access grants
- Repository-level permissions (Issues: Read & Write, Contents: Read & Write, etc.)
- Possible org admin approval

**Setting Up gh CLI:**

```bash
# Install gh CLI
brew install gh  # macOS
# or download from https://cli.github.com/

# Authenticate with token
echo "your-token-here" | gh auth login --with-token

# Verify authentication
gh auth status

# Store token in ~/.env for safekeeping
echo "GITHUB_TOKEN=your-token-here" >> ~/.env
```

**Common gh CLI Commands for Maintenance:**

```bash
# PR Management
gh pr list                                    # List open PRs
gh pr view 4                                  # View PR #4
gh pr comment 4 --body "@dependabot rebase"  # Comment on PR
gh pr merge 4 --squash                        # Merge PR

# Workflow Management  
gh run list --limit 5                         # Recent workflow runs
gh run view <run-id>                          # View run details
gh run rerun <run-id>                         # Rerun failed workflow
gh run view <run-id> --log-failed             # View failure logs

# Secrets Management
gh secret list                                # List repo secrets
gh secret set SECRET_NAME --body "value"      # Set secret
gh secret delete SECRET_NAME                  # Delete secret

# Release Management
gh release create v0.X.Y --title "Release v0.X.Y" --notes "Release notes"
gh release list
```

**Token Permissions Required:**

For full maintenance access, ensure token has:
- ✅ `repo` (Full control of private repositories)
- ✅ `workflow` (Update GitHub Action workflows) 
- ✅ `write:packages` (if publishing packages)

**Security Best Practices:**

1. **Store tokens securely:**
   ```bash
   # Add to ~/.env (in .gitignore)
   echo "GITHUB_TOKEN=ghp_..." >> ~/.env
   echo "SONAR_TOKEN=..." >> ~/.env
   
   # Never commit tokens to repository
   ```

2. **Use minimal permissions:** Only grant what's needed

3. **Rotate tokens regularly:** Generate new tokens every 90 days

4. **Use GitHub Secrets for CI/CD:** Never hardcode tokens in workflows

### PyPI

**Package:** https://pypi.org/project/beast-mailbox-core/

**Publishing:** Use `twine upload dist/*`

**Credentials:** Stored in `~/.pypirc` or use environment variables:
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-...token...
```

### pytest Configuration

**Location:** `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"  # Critical for async tests
addopts = [
  "--cov=src/beast_mailbox_core",
  "--cov-report=xml",
  "--cov-report=term-missing",
  "--verbose",
]
```

**Key Feature:** `asyncio_mode = "auto"` enables seamless async test execution.

---

## Critical Lessons from History

### Lesson 1: Repository is Source of Truth

**Context:** v0.2.0 was published without committing, creating a critical sync failure.

**Rule:** ALWAYS commit → tag → push → then publish. Never reverse this order.

### Lesson 2: Tests ≥ Cognitive Complexity

**Context:** Industry best practice discovered during v0.3.0 development.

**Rule:** Maintain at least one test per unit of cognitive complexity. Currently 59 tests for 47 complexity (125%).

### Lesson 3: Documentation Density Matters

**Context:** Went from 8.3% to 52.2% documentation density.

**Impact:** Transformed maintainability. AI agents and humans can understand code much faster.

**Rule:** Aim for 40%+ comment density. Include examples, design decisions, and context.

### Lesson 4: Some Code is Intentionally Untestable

**Context:** Infinite event loops can't be unit tested.

**Acceptance:** 90% coverage with 100% testable code covered is excellent.

**Rule:** Don't compromise architecture for metrics. Accept architectural limitations.

### Lesson 5: Engage with Quality Tools, Don't Just Suppress

**Context:** Even SonarCloud "false positives" led to improvements (e.g., adding `await client.ping()` for connection validation).

**Rule:** Understand why tools flag issues. Fix when reasonable, document when not.

### Lesson 6: AsyncIO CancelledError Must Be Re-Raised

**Pattern:**
```python
try:
    await some_operation()
except asyncio.CancelledError:
    raise  # Always re-raise unless you're the cleanup handler
except Exception:
    logging.exception("...")
```

**Exception:** In cleanup methods like `stop()`, you ARE the cancellation handler, so suppression is correct.

### Lesson 7: Small, Frequent Releases Build Confidence

**Context:** 7 releases in one session, each with one clear improvement.

**Result:** Each release was a checkpoint, reducing risk.

**Rule:** Release early, release often. Each release should have a clear purpose.

### Lesson 8: False CHANGELOG Claims Destroy Trust

**Context:** v0.2.0 claimed "21 tests" when zero existed.

**Rule:** Always verify claims. Run tests, count output, use actual numbers.

### Lesson 9: Editable Install for Development

**Pattern:**
```bash
pip install -e .
```

**Why:** Enables accurate coverage measurement and immediate feedback during development.

**Rule:** Always use editable install during development.

### Lesson 10: Quality is a Choice, Not a Circumstance

**Context:** Project went from broken (0% coverage) to best-in-class (90% coverage, 52% docs, 0 defects) in one session.

**Proof:** Excellence is achievable through systematic pursuit of quality.

**Rule:** Choose excellence. Use tools to enforce standards. Iterate rapidly.

### Lesson 11: Use the Correct GitHub Actions for Third-Party Services

**Context:** SonarCloud workflow was failing with `SONAR_TOKEN` errors despite token being set.

**Root Cause:** Using `SonarSource/sonarqube-scan-action@v6` (for self-hosted SonarQube) instead of `SonarSource/sonarcloud-github-action@master` (for SonarCloud).

**Impact:** Authentication mechanisms differ between the two actions. Wrong action = guaranteed failure.

**Rule:** Always use service-specific GitHub Actions. Read the official docs for the correct action name.

### Lesson 12: Classic GitHub Tokens > Fine-Grained for Organization Repos

**Context:** Spent significant time debugging fine-grained token permissions for organization repo.

**Issue:** Fine-grained tokens require:
- Explicit per-repository access configuration
- Organization admin approval (even if you're the admin)
- Repository-specific permissions (Issues, Contents, etc.)

**Solution:** Classic tokens with `repo` scope work immediately for org repos.

**Rule:** For AI agents maintaining organization repos, use classic tokens (`ghp_...`). Fine-grained tokens add unnecessary complexity.

**Note:** This isn't a security issue - classic tokens are still fully supported and appropriate for automation.

### Lesson 13: GitHub Secrets Must Be Actually Set

**Context:** Workflow was reading `SONAR_TOKEN` as empty despite thinking it was configured.

**Debugging:** Used `gh secret list` to verify existence, then `gh secret set` to update value.

**Common Causes:**
- Secret set with empty value
- Secret not saved after editing
- Token permissions insufficient (secret exists but value is invalid)

**Rule:** Always verify secrets after setting:
```bash
gh secret set SECRET_NAME --body "value"
gh secret list  # Verify it appears with recent timestamp
```

---

## Troubleshooting Guide

### Tests Failing

**Problem:** Tests fail after changes

**Debug Steps:**
```bash
# 1. Run specific failing test with verbose output
pytest tests/test_file.py::TestClass::test_name -v

# 2. Check for async issues
pytest tests/ --log-cli-level=DEBUG

# 3. Verify fixtures are correct
# Check conftest.py for fixture definitions

# 4. Check mocking
# Ensure patch target is import location, not definition
```

**Common Causes:**
- AsyncMock not used for async functions
- Patching wrong location (use import location)
- Fixtures not properly cleaned up
- Real tasks needed instead of mocks for cancellation

### Coverage Dropping

**Problem:** Coverage falls below 85%

**Debug Steps:**
```bash
# 1. Generate detailed coverage report
pytest tests/ --cov --cov-report=html
open htmlcov/index.html

# 2. Find uncovered lines
pytest tests/ --cov --cov-report=term-missing

# 3. Add tests for uncovered code
vim tests/test_missing_coverage.py
```

**Common Causes:**
- New code added without tests
- Exception handlers not tested
- Edge cases missing

### SonarCloud Quality Gate Failing

**Problem:** Quality Gate fails on push

**Debug Steps:**
1. Check SonarCloud dashboard
2. Review new code metrics (not overall)
3. Check for:
   - New bugs
   - New code smells
   - Coverage of new code < 80%
   - Security hotspots

**Common Fixes:**
- Add tests for new code
- Refactor complex functions (complexity > 15)
- Fix bugs identified
- Document intentional design decisions

### Redis Connection Issues

**Problem:** Tests fail with Redis connection errors

**Solution:** Tests use mocks - shouldn't connect to real Redis.

**Check:**
```python
# Verify mocking
with patch('beast_mailbox_core.redis_mailbox.redis.Redis', return_value=mock_client):
    # Your test code
```

### Package Build Failing

**Problem:** `python -m build` fails

**Debug Steps:**
```bash
# 1. Check pyproject.toml syntax
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"

# 2. Verify all source files exist
ls -la src/beast_mailbox_core/

# 3. Clean and retry
rm -rf dist/ build/ *.egg-info
python -m build
```

### SonarCloud Workflow Failing

**Problem:** GitHub Actions workflow fails on SonarCloud step

**Error 1: "Running this GitHub Action without SONAR_TOKEN is not recommended" + HTTP 401**

**Debug Steps:**
```bash
# 1. Verify secret exists
gh secret list --repo nkllon/beast-mailbox-core | grep SONAR

# 2. Check secret timestamp (should be recent)
# If old or missing, regenerate and set:

# 3. Generate new token at https://sonarcloud.io/account/security

# 4. Set secret
gh secret set SONAR_TOKEN --body "your-sonar-token" --repo nkllon/beast-mailbox-core

# 5. Re-run workflow
gh run rerun <run-id>
```

**Error 2: "Resource not accessible by personal access token"**

**Cause:** Using wrong GitHub Action for SonarCloud

**Fix:** Update `.github/workflows/sonarcloud.yml`:
```yaml
# ❌ WRONG - This is for self-hosted SonarQube
uses: SonarSource/sonarqube-scan-action@v6

# ✅ CORRECT - This is for SonarCloud
uses: SonarSource/sonarcloud-github-action@master
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

**Error 3: Quality Gate failing**

**Debug:**
1. Visit https://sonarcloud.io/project/overview?id=nkllon_beast-mailbox-core
2. Check "New Code" tab (not "Overall Code")
3. Review:
   - Coverage of new code (must be ≥ 80%)
   - New bugs (must be 0)
   - New code smells (should be 0)
4. Fix issues in new code and push again

### GitHub CLI Authentication Issues

**Problem:** `gh` commands fail with authentication errors

**Error: "To get started with GitHub CLI, please run: gh auth login"**

**Solution:**
```bash
# 1. Get/create classic token at https://github.com/settings/tokens/new
# Check "repo" scope

# 2. Authenticate
echo "ghp_your_token_here" | gh auth login --with-token

# 3. Verify
gh auth status
```

**Error: "GraphQL: Resource not accessible by personal access token"**

**For Organization Repos:**

This usually means using a fine-grained token without proper permissions.

**Fix:**
```bash
# Use a classic token instead
# 1. Go to https://github.com/settings/tokens/new
# 2. Check "repo" scope
# 3. Generate token
# 4. Authenticate:
echo "ghp_new_token" | gh auth login --with-token
```

**Or configure fine-grained token properly:**
1. Go to https://github.com/settings/personal-access-tokens/active
2. Click your token
3. Repository access: Add `nkllon/beast-mailbox-core`
4. Permissions → Issues: Read and write
5. Permissions → Contents: Read and write
6. Save changes
7. **Important:** Regenerate token (permission changes require regeneration)

---

## Quick Reference

### Essential Commands

```bash
# Development
pip install -e ".[dev]"           # Install for development
pytest tests/                     # Run all tests
pytest tests/ --cov              # Run with coverage
python -m build                  # Build package

# Release
git tag -a v0.X.Y -m "Release"   # Create tag
twine upload dist/*              # Upload to PyPI

# Quality
pytest tests/ --cov-report=html  # Generate coverage HTML
# Visit SonarCloud for quality metrics

# Redis operations (manual testing)
redis-cli XLEN beast:mailbox:test:in
redis-cli XREVRANGE beast:mailbox:test:in + - COUNT 5
```

### Key Metrics to Monitor

| Metric | Target | Command |
|--------|--------|---------|
| Tests | ≥ Complexity | `pytest tests/ -v \| grep "passed"` |
| Coverage | ≥ 85% | `pytest tests/ --cov` |
| Quality Gate | PASSED | Visit SonarCloud |
| Bugs | 0 | Visit SonarCloud |

### Important URLs

- **GitHub:** https://github.com/nkllon/beast-mailbox-core
- **PyPI:** https://pypi.org/project/beast-mailbox-core/
- **SonarCloud:** https://sonarcloud.io/project/overview?id=nkllon_beast-mailbox-core

### Key Files to Remember

| File | Purpose |
|------|---------|
| `pyproject.toml` | Package metadata, version, dependencies |
| `CHANGELOG.md` | Release notes (update before release) |
| `README.md` | User documentation |
| `steering/release-procedure-CORRECTED.md` | Release checklist |
| `docs/LESSONS_LEARNED_v0.3.0.md` | Historical context |
| `AGENT.md` (this file) | Maintainer guide |

### Contact & Escalation

**For Issues:**
1. Check this guide
2. Review `docs/LESSONS_LEARNED_v0.3.0.md`
3. Check GitHub Issues
4. Review previous PR discussions
5. Consult user (if critical decision needed)

---

## Maintenance Philosophy

### Core Principles

1. **Quality First:** Never compromise on quality for speed
2. **Test Everything:** If it's testable, it must be tested
3. **Document Thoroughly:** Explain why, not just what
4. **Release Carefully:** Follow the checklist, every time
5. **Learn Continuously:** Update this guide with new lessons
6. **User Focus:** Users depend on this library - respect that trust

### Decision Framework

**When making decisions:**

1. **Will this break existing users?**
   - If yes, needs major version bump (semantic versioning)
   - Add deprecation warnings before breaking changes

2. **Does this maintain quality standards?**
   - Check tests, coverage, documentation
   - Run SonarCloud scan

3. **Is this well-documented?**
   - Update README, docstrings, CHANGELOG
   - Include examples

4. **Can this be tested?**
   - If yes, write tests
   - If no, document why

5. **Does this align with project goals?**
   - Inter-agent messaging via Redis
   - Simple, reliable, well-documented

---

## Version History Summary

| Version | Date | Key Achievement |
|---------|------|-----------------|
| 0.1.0 | Initial | Basic functionality |
| 0.2.0 | 2025-10-10 | Added `--ack` and `--trim` (sync crisis) |
| 0.2.1-0.2.5 | 2025-10-10 | Quality improvements, testing |
| 0.3.0 | 2025-10-10 | Excellence Edition (52% docs, 52 tests) |
| 0.3.1 | 2025-10-10 | 90% Coverage Milestone (59 tests) |

---

## Final Notes

### What Makes This Project Special

1. **Built by AI, for AI:** Entire codebase designed and implemented by LLMs
2. **Best-in-Class Quality:** Exceeds industry standards in every metric
3. **Comprehensive Documentation:** 52% comment density (208% of standard)
4. **Battle-Tested:** Recovered from critical crisis, now rock-solid
5. **Living Example:** Demonstrates what's possible with AI development

### Your Responsibility

As maintainer, you are responsible for:
- Preserving quality standards (don't let them slip!)
- Following release procedures (protect users!)
- Maintaining documentation (help future maintainers!)
- Learning from issues (update this guide!)
- Being responsive to users (they depend on this!)

### Continuous Improvement

This guide should evolve. When you learn something new:

1. Update this file
2. Commit with clear message: `docs: update AGENT.md with lesson about X`
3. Consider if other docs need updating too

### Success Metrics

You're succeeding as maintainer if:
- ✅ All quality metrics remain in "excellent" range
- ✅ Users report satisfaction (few issues, quick resolutions)
- ✅ No release incidents (no sync failures, no breaking changes)
- ✅ Documentation stays current
- ✅ Test suite grows with codebase
- ✅ This guide stays accurate and helpful

---

## Welcome Aboard! 🚀

You're now equipped to maintain Beast Mailbox Core with confidence. This project has come a long way from its crisis to excellence. Your job is to keep it excellent and make it even better.

**Remember:**
- Quality is non-negotiable
- Tests are your safety net
- Documentation is for future you
- Users trust this library
- Excellence is a choice

Good luck, and may your coverage always be ≥ 85%! 📊✨

---

**Last Updated:** 2025-10-14  
**Maintained By:** AI Agent (You)  
**Previous Maintainer:** Herbert (AI Agent)  
**Document Version:** 1.1.0

**Changes in v1.1.0:**
- Added comprehensive GitHub Tokens & gh CLI section
- Added SonarCloud workflow troubleshooting
- Added lessons about correct GitHub Actions usage
- Added lessons about Classic vs Fine-Grained tokens for org repos
- Added debugging steps for authentication issues

**Questions?** Check `docs/LESSONS_LEARNED_v0.3.0.md` for 80+ specific lessons learned.

