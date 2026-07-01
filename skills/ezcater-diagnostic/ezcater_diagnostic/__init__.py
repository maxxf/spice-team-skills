"""ezCater catering diagnostic — deterministic scoring core.

Catering analog of the delivery `client-diagnostics` orchestrator, compressed to a
single self-contained package. Sub-buckets: Ops · Visibility · Packaging.

See references/ezcater-diagnostic-framework.md for the methodology.
"""

from ezcater_diagnostic.run import run_diagnostic

__all__ = ["run_diagnostic"]
