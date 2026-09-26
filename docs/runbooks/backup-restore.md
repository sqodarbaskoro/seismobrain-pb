# Runbook: Backup and restore

**Author:** Sri Yanto Qodarbaskoro  
**Date:** 2026-09-16

> **Status:** the backup and restore scripts are currently smoke-test scaffolds. They copy only the Starter `data/` directory, do not back up PostgreSQL or Qdrant, and write a `consistency.json` that is not derived from real checks.

```bash
npm run backup -- --tier production --smoke
npm run restore -- --tier production --fresh-cluster --verify-drill
```

Verify `consistency.json` (metadata, vectors, aliases) before declaring success.
