# Beast Orchestrator

[![PyPI version](https://img.shields.io/pypi/v/beast-orchestrator?label=PyPI&color=blue)](https://pypi.org/project/beast-orchestrator/)
[![Python Versions](https://img.shields.io/pypi/pyversions/beast-orchestrator.svg)](https://pypi.org/project/beast-orchestrator/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Orchestrates and coordinates work across multiple LLM nodes in Beast Mode cluster**

## Status

🚧 **Under Development** - This project is being built using AI-driven spec-driven development.

## Overview

Beast Orchestrator is the **coordination layer** for Beast Mode clusters:
- Assigns tasks to appropriate LLM nodes
- Coordinates multi-agent workflows
- Manages task queues and priorities
- Monitors node health and capacity
- Handles failover and load balancing

## Architecture

```
┌─────────────────────────────────────────────────┐
│          Beast Orchestrator                      │
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │  Task Queue & Scheduler                   │  │
│  │  - Assign tasks to nodes                  │  │
│  │  - Monitor progress                       │  │
│  │  - Handle failures                        │  │
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

## Features

- **Task Scheduling** - Intelligent task assignment to nodes
- **Load Balancing** - Distribute work based on capacity
- **Health Monitoring** - Track node status and availability
- **Workflow Management** - Coordinate multi-step workflows
- **Failover Handling** - Automatically retry failed tasks
- **Priority Queue** - Urgent tasks get handled first

## Installation

```bash
pip install beast-orchestrator
```

## Usage

```bash
# Start the orchestrator
beast-orchestrator \
  --redis-host vonnegut \
  --redis-password beastmode2025 \
  --scheduler round-robin \
  --max-retries 3
```

## Development Status

This project follows **spec-driven development**. See [`.spec-workflow/`](.spec-workflow/) for:
- Requirements specifications
- Design documents
- Implementation plans

## For AI Maintainers

**This repository is built 100% by AI agents and maintained by AI agents.**

Start here:
- **📖 [AGENT.md](AGENT.md)** - Comprehensive maintainer guide
- **📁 [.spec-workflow/](.spec-workflow/)** - Specifications and requirements

## Quality Standards

This project maintains the same quality standards as beast-mailbox-core:
- ✅ ≥ 85% test coverage
- ✅ Zero defects (SonarCloud)
- ✅ Comprehensive documentation
- ✅ All tests passing

## License

MIT

---

**Built with ❤️ by AI agents for Beast Mode orchestration**

