# Runbook: Air-gapped deployment

**Author:** Sri Yanto Qodarbaskoro  
**Date:** 2026-09-16

```bash
npm run docker:up -- --air-gapped
npm run egress:test
```

Default-deny egress NetworkPolicies apply in Production Helm (`networkPolicy.airGapped: true`).
Offline model bundles required; no external DNS from application pods.
