# Sizing

**Author:** Sri Yanto Qodarbaskoro  
**NFR:** NFR-MAINT-01  
**Date:** 2026-09-16

## Planning defaults

- Chunks ≈ pages × 3
- Dense vector RAM ≈ vectors × dimension × 4 bytes × 1.5 (before quantization)
- Team: start with 2 API replicas; enable PgBouncer above 4 API replicas
- Production: separate pools for API, workers, models, and data

See also Helm `values.yaml` resource and replica defaults.
