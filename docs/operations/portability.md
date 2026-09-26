# Portability

**Author:** Sri Yanto Qodarbaskoro  
**Date:** 2026-09-16  
**NFR:** NFR-PORT-01

## Container images

SeismoBrain Production and Team container images build for:

- `linux/amd64` (x86_64)
- `linux/arm64`

Build with:

```bash
npm run docker:build -- --platform linux/amd64,linux/arm64 --smoke
```

All base images are digest-pinned (no `latest` tags).

## Starter and development hosts

| OS | Starter | Development notes |
|---|---|---|
| Linux (amd64/arm64) | Supported | Preferred for Team/Production parity |
| macOS | Supported for Starter and local development | Docker Desktop or Colima for Team Compose |
| Windows | Supported for Starter and local development | WSL2 recommended for Docker-based Team profile |

CPU-only operation is supported in every tier (NFR-PORT-02).
