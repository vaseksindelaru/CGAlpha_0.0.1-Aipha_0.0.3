"""
cgalpha.domain — Pure domain layer.

This package contains:
- models/: Entities and Value Objects (frozen dataclasses)
- ports/:  Interface contracts (Protocol classes)
- services/: Domain services (pure logic, no I/O) [Phase 2.2+]

INVARIANT: This package has ZERO external dependencies.
           Only stdlib + typing imports are allowed.
"""
