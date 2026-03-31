# Interview Talking Points — Hospital Bed Occupancy Monitor

## For Every Component: Why, Scale, Quality, Hindsight, Domain

---

## 1. Data Simulator
**Why this technology?** Python for rapid prototyping of realistic healthcare event patterns. Built configurable time-of-day/day-of-week multipliers because real hospital admissions follow circadian patterns.

**What breaks at 10x scale?** Single-threaded generator becomes a bottleneck. Solution: Use multiprocessing with one generator per ward, or switch to Apache Kafka Connect with a custom HL7 source connector.

**Data quality issue?** Early versions generated patients admitted to full wards. Added bed tracking to prevent impossible states.

**Do differently?** Would use Faker library for patient demographics and add realistic ICD-10 diagnosis codes instead of simple categories.

**Healthcare constraint:** Event ordering matters — you can't discharge a patient before admitting them. The simulator enforces admission-before-discharge invariant per patient.

---

## 2. Kafka
**Why?** Kafka provides exactly-once semantics and durable message storage, critical in healthcare where every ADT event is a legal record. 7-day retention matches our baseline window.

**At 10x scale?** Increase partitions from 7 to 21+ (3 per ward), add consumer groups for parallel processing, deploy multi-broker cluster.

**Quality issue?** Consumer lag during spike simulation. Fixed by increasing batch size and tuning `max.poll.records`.

**Do differently?** Would use Azure Event Hubs in production (Kafka-compatible, managed service, HIPAA-compliant).

**Healthcare constraint:** Message ordering per ward is critical. Partition key = ward_id ensures all events for one ward go to same partition.

---

## 3. PySpark (Medallion Architecture)
**Why Bronze/Silver/Gold?** Separating raw data (Bronze) from cleaned (Silver) from aggregated (Gold) enables reprocessing without re-ingesting. Essential when data quality rules evolve.

**At 10x scale?** Move from local Spark to Databricks with auto-scaling clusters. Switch from Parquet to Delta Lake for ACID transactions. Use Structured Streaming instead of batch.

**Quality issue?** Duplicate admissions: a bug initially allowed patients in two wards simultaneously. Silver layer deduplication rule catches this.

**Do differently?** Would implement schema evolution handling (new HL7 fields) using Delta Lake schema merge.

**Healthcare constraint:** Late-arriving events are common (nurse documents discharge 2 hours later). Silver layer flags but doesn't reject them, preserving data completeness.

---

## 4. Airflow
**Why?** Airflow provides visible DAG dependencies, retry logic, and scheduling — all critical for operational pipelines where failures must be tracked and resolved.

**At 10x scale?** Use CeleryExecutor or KubernetesExecutor instead of LocalExecutor. Move to managed Airflow (MWAA or Cloud Composer).

**Quality issue?** DAG 3 (SLA monitoring) initially ran every 5 minutes, causing SQLite lock contention. Changed to 15 minutes.

**Do differently?** Would use Airflow sensors to check Kafka consumer lag before triggering Spark jobs, avoiding processing empty batches.

**Healthcare constraint:** SLA monitoring DAG is the most important — a ward above 85% for 2+ hours represents patient safety risk, not just a KPI miss. That's why it runs 4x more frequently than the hourly snapshot.

---

## 5. LLM (Claude) Integration
**Why?** Charge nurses don't have time to interpret dashboards. A natural language explanation of "why is Emergency at 93%?" saves cognitive load during high-stress situations.

**At 10x scale?** Implement prompt caching for repeated patterns, batch similar alerts, use streaming responses.

**Quality issue?** Early prompts produced generic responses. Adding specific numbers (z-score, baseline, trend direction) to the prompt dramatically improved output quality.

**Do differently?** Would fine-tune a smaller model on historical breach explanations to reduce API costs and latency.

**Healthcare constraint:** Fallback mechanism is non-negotiable — if the API is down, nurses still need an explanation. Rule-based fallback ensures 100% coverage.

---

## 6. FastAPI
**Why?** FastAPI gives automatic OpenAPI docs, Pydantic validation, async support (needed for WebSocket), and high performance.

**At 10x scale?** Add Redis caching layer for frequently-queried ward state. Use PostgreSQL instead of SQLite. Deploy behind load balancer with multiple uvicorn workers.

**Quality issue?** WebSocket reconnection was dropping alerts during network blips. Added heartbeat mechanism and client-side reconnection logic.

**Do differently?** Would add authentication (JWT) and RBAC — different roles (nurse, administrator, bed manager) need different views.

**Healthcare constraint:** WebSocket latency matters — a 30-second delay in alert delivery could mean 30 seconds of a nurse not knowing about a critical bed shortage.

---

## 7. React Dashboard
**Why?** React's component model maps perfectly to the dashboard hierarchy: WardGrid → WardCard → OccupancyGauge. Recharts provides the trend visualization.

**At 10x scale?** Implement virtual scrolling for the alert feed, add service worker for offline capability, consider React Server Components.

**Quality issue?** Gauge animation was janky during rapid updates. Fixed by using CSS transitions instead of React state-driven animation.

**Do differently?** Would add role-based views (charge nurse sees their ward prioritized, bed manager sees cross-hospital view).

**Healthcare constraint:** Color scheme follows medical convention: green=normal, yellow=caution, red=critical. Tablet-responsive because charge nurses use tablets during rounds.

---

## 8. Azure + Databricks
**Why Azure?** ADLS Gen2 + Databricks + Azure SQL form a complete lakehouse architecture. ADLS handles raw data lake, Databricks processes, Azure SQL serves analytics.

**Why Delta Lake over Parquet?** ACID transactions prevent corrupted reads during writes. Time travel enables auditing — "what was the occupancy on March 15th?" is a single query.

**Why ZORDER?** Query access pattern is always ward_id + timestamp. ZORDER co-locates this data physically, reducing I/O by 60-80%.

---

## Key Numbers to Memorize
- 7 wards, 190 total beds
- 85% SLA threshold, 2-hour consecutive breach window
- Z-score threshold: 2.5 (99.4th percentile)
- 7-day rolling baseline window
- ~50 events/hour normal, ~150 events/hour during spike
- 5 data quality rules in Silver layer
- 3 Airflow DAGs (hourly, daily, 15-min SLA)
