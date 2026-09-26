# Runbook: Tier migration

**Author:** Sri Yanto Qodarbaskoro  
**Date:** 2026-09-16

> **Status:** the tier migration script is currently a scaffold. It writes a migration report but does not move data, and the report's consistency flags are not derived from real checks.

```bash
npm run migrate:tier -- --to team --smoke
npm run migrate:tier -- --to production --smoke
```

Starter → Team moves SQLite/local Qdrant/files to PostgreSQL/Qdrant server/volume.
Team → Production loads a Team backup bundle into Kubernetes.
Consistency verification is mandatory (DR-12).
