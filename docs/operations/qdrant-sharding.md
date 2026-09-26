# Qdrant sharding and replication

**Author:** Sri Yanto Qodarbaskoro  
**NFR:** NFR-SCALE-03  
**Date:** 2026-09-16

SeismoBrain supports Qdrant sharding and replication **without application changes**.
The API and workers address collections through the active alias; shard topology is
configured on the Qdrant cluster (Helm `qdrant.shards` / `qdrant.replicationFactor`).

Smoke on kind/cluster: set `shards ≥ 1` and `replicationFactor ≥ 1` in values, deploy,
and confirm search via `seismobrain_chunks_active` still returns points.
