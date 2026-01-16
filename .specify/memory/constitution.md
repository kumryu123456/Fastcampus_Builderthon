<!--
================================================================================
SYNC IMPACT REPORT
================================================================================
Version Change: [TEMPLATE] → 1.0.0 (Initial Release)
Modified Principles: All principles are new
Added Sections: Core Principles (5), Development Workflow, Governance
Removed Sections: None
Templates Status:
  ✅ plan-template.md - Constitution Check section compatible
  ✅ spec-template.md - Requirements align with principles
  ✅ tasks-template.md - Task structure supports testing & MVP approach
Follow-up TODOs:
  - Define specific retry logic patterns for Claude/ElevenLabs (Principle II)
  - Establish structured logging standards (Principle V)
  - Set up credential scanning tools (Principle III)
================================================================================
-->

# PathPilot Constitution

## Core Principles

### I. Agentic AI First

All workflows and automation MUST be built using LangGraph for autonomous agent orchestration. This ensures:
- Workflows are modular, stateful, and debuggable
- Agents can make autonomous decisions within defined boundaries
- System behavior is predictable and auditable through graph-based execution

**Rationale**: LangGraph provides the foundation for building reliable, maintainable agentic systems that can scale from simple automation to complex multi-agent workflows.

### II. External API Resilience

ALL external API calls to Claude, ElevenLabs, and other third-party services MUST implement retry logic with exponential backoff. Required patterns:
- Minimum 3 retry attempts with exponential backoff
- Circuit breaker pattern for sustained failures
- Graceful degradation when services are unavailable
- Clear timeout definitions for all API calls

**Rationale**: External services are unreliable by nature. Retry logic prevents transient failures from breaking user experiences during the hackathon demo and beyond.

### III. User Data Privacy (NON-NEGOTIABLE)

User credentials and sensitive data MUST NEVER be leaked, logged, or exposed. Requirements:
- API keys and credentials stored in environment variables only
- No sensitive data in logs, error messages, or stack traces
- Credential scanning in pre-commit hooks
- Secure storage patterns for user-generated content
- Explicit data handling documentation for all components

**Rationale**: Privacy breaches destroy user trust and can disqualify projects from competitions. Security is not negotiable.

### IV. Hackathon MVP First

Development MUST prioritize a working 2-day MVP with core features only. This means:
- Build the smallest feature set that demonstrates value
- No premature optimization or gold-plating
- Focus on the demo story: what will we show on stage?
- Technical debt is acceptable if documented
- "Nice-to-have" features are explicitly deferred

**Rationale**: Hackathons reward completed demos, not perfect codebases. Ship fast, iterate later.

### V. Code Quality

All code MUST maintain minimum 80% test coverage and implement structured logging. Standards:
- Unit tests for business logic (target: 80%+ coverage)
- Integration tests for API contracts and external services
- Structured logging with consistent log levels (DEBUG, INFO, WARNING, ERROR)
- Log context includes request IDs, user IDs (anonymized), and operation names
- Code reviews verify both test coverage and logging completeness

**Rationale**: Quality gates prevent regressions during rapid development. Good logging is essential for debugging agentic systems where behavior is emergent.

## Development Workflow

### Feature Development Process

1. **Planning**: Every feature starts with a specification (spec.md) and implementation plan (plan.md)
2. **Test-First**: Write tests that capture acceptance criteria before implementation
3. **Implementation**: Build the minimum code to pass tests and meet requirements
4. **Review**: Verify constitution compliance, test coverage, and logging standards
5. **Integration**: Merge to main after passing all quality gates

### Quality Gates

Before merging any feature:
- [ ] All tests pass (unit + integration)
- [ ] Test coverage meets 80% minimum threshold
- [ ] External API calls have retry logic implemented
- [ ] No credentials or sensitive data in code or logs
- [ ] Structured logging added for key operations
- [ ] Constitution compliance verified

### Hackathon Prioritization

During the 2-day hackathon window:
- P1 (Critical): Core demo functionality - MUST be complete
- P2 (Important): Enhanced user experience - SHOULD be complete if time permits
- P3 (Nice-to-have): Polish and edge cases - DEFERRED unless trivial

## Governance

### Amendment Process

1. Proposed changes must be documented with rationale
2. Team consensus required for principle changes
3. Version incremented according to semantic versioning:
   - MAJOR: Breaking changes to principles or removal of core requirements
   - MINOR: New principles added or material expansions to existing guidance
   - PATCH: Clarifications, wording improvements, non-semantic fixes

### Compliance

- Constitution supersedes all other development practices
- All code reviews MUST verify constitutional compliance
- Violations require explicit justification and team approval
- Complexity that violates principles must be justified in plan.md

### Version Control

**Version**: 1.0.0 | **Ratified**: 2025-01-16 | **Last Amended**: 2025-01-16
