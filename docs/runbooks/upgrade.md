# Runbook: Upgrade

**Author:** Sri Yanto Qodarbaskoro  
**Date:** 2026-09-16

> **Status:** the upgrade script is currently a smoke-test scaffold. The image update, restart, and readiness steps are placeholders.

```bash
npm run upgrade -- --dry-run-smoke
```

Sequence: backup → image update → migrate → restart → readiness → smoke evaluation.
Stops on failure with rollback instructions.
