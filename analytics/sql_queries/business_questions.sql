-- ═══════════════════════════════════════════════════════════════════════════
-- 15 SQL Business Questions — Hospital Bed Occupancy Analytics
-- Run against Azure SQL or SQLite (Gold layer tables)
-- ═══════════════════════════════════════════════════════════════════════════

-- ─── SIMPLE QUERIES ────────────────────────────────────────────────────────

-- Q1: Which ward had the highest average occupancy last week?
-- Purpose: Identify consistently over-burdened wards for resource planning.
SELECT ward_name, 
       ROUND(AVG(occupancy_percent), 1) AS avg_occupancy
FROM ward_occupancy_hourly
WHERE snapshot_hour >= DATE('now', '-7 days')
GROUP BY ward_name
ORDER BY avg_occupancy DESC
LIMIT 1;


-- Q2: What is the current bed availability across all wards?
-- Purpose: Real-time capacity overview for bed management.
SELECT ward_name, total_beds, occupied_beds,
       (total_beds - occupied_beds) AS available_beds,
       occupancy_percent, status
FROM ward_occupancy_current
ORDER BY occupancy_percent DESC;


-- Q3: How many SLA breaches occurred in the past 30 days by ward?
-- Purpose: Track compliance trends for hospital accreditation reporting.
SELECT ward_name, 
       COUNT(*) AS breach_count,
       ROUND(AVG(consecutive_hours), 1) AS avg_breach_duration_hrs
FROM sla_breaches
WHERE breach_start_time >= DATE('now', '-30 days')
GROUP BY ward_name
ORDER BY breach_count DESC;


-- ─── MEDIUM COMPLEXITY ─────────────────────────────────────────────────────

-- Q4: Which hours of the day consistently exceed 85% across all wards?
-- Purpose: Identify systemic peak hours for staffing optimization.
SELECT hour_of_day,
       COUNT(DISTINCT ward_id) AS wards_above_85,
       ROUND(AVG(baseline_avg_occupancy), 1) AS avg_occupancy_at_hour,
       GROUP_CONCAT(DISTINCT ward_name) AS affected_wards
FROM ward_baseline
WHERE baseline_avg_occupancy >= 85
GROUP BY hour_of_day
HAVING wards_above_85 >= 2
ORDER BY wards_above_85 DESC, hour_of_day;


-- Q5: What is the average admission rate per ward per day of week?
-- Purpose: Predict demand patterns for elective surgery scheduling.
SELECT w.ward_name,
       CASE CAST(strftime('%w', h.snapshot_hour) AS INTEGER)
           WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday'
           WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday'
           WHEN 5 THEN 'Friday' WHEN 6 THEN 'Saturday'
       END AS day_of_week,
       ROUND(AVG(h.admits_count), 1) AS avg_hourly_admits,
       SUM(h.admits_count) AS total_admits
FROM ward_occupancy_hourly h
JOIN wards w ON h.ward_id = w.ward_id
WHERE h.snapshot_hour >= DATE('now', '-30 days')
GROUP BY w.ward_name, strftime('%w', h.snapshot_hour)
ORDER BY w.ward_name, CAST(strftime('%w', h.snapshot_hour) AS INTEGER);


-- Q6: Which wards had the most anomaly detections?
-- Purpose: Identify wards prone to unexpected surges for contingency planning.
SELECT ward_name,
       COUNT(*) AS total_anomalies,
       ROUND(MAX(z_score), 2) AS peak_z_score,
       ROUND(AVG(z_score), 2) AS avg_z_score,
       MAX(detection_time) AS last_anomaly
FROM anomaly_flags
WHERE is_anomaly = 1
GROUP BY ward_name
ORDER BY total_anomalies DESC;


-- Q7: What is the peak-to-trough occupancy range per ward?
-- Purpose: Measure ward volatility — high range = unpredictable demand.
SELECT ward_name,
       ROUND(MAX(peak_occupancy_percent), 1) AS highest_peak,
       ROUND(MIN(min_occupancy_percent), 1) AS lowest_trough,
       ROUND(MAX(peak_occupancy_percent) - MIN(min_occupancy_percent), 1) AS range_pct,
       ROUND(AVG(avg_occupancy_percent), 1) AS avg_daily_occ
FROM ward_occupancy_daily
WHERE report_date >= DATE('now', '-30 days')
GROUP BY ward_name
ORDER BY range_pct DESC;


-- ─── COMPLEX QUERIES ───────────────────────────────────────────────────────

-- Q8: Average time from first breach to resolution per ward.
-- Purpose: Measure response effectiveness — fast resolution = good ops.
SELECT ward_name,
       COUNT(*) AS total_breaches,
       ROUND(AVG(
           (julianday(COALESCE(resolved_at, datetime('now'))) 
            - julianday(breach_start_time)) * 24
       ), 1) AS avg_resolution_hours,
       ROUND(MIN(
           (julianday(COALESCE(resolved_at, datetime('now'))) 
            - julianday(breach_start_time)) * 24
       ), 1) AS fastest_resolution_hrs,
       ROUND(MAX(
           (julianday(COALESCE(resolved_at, datetime('now'))) 
            - julianday(breach_start_time)) * 24
       ), 1) AS slowest_resolution_hrs
FROM sla_breaches
WHERE status = 'resolved'
GROUP BY ward_name
ORDER BY avg_resolution_hours DESC;


-- Q9: Consecutive days a ward stayed above 70% occupancy.
-- Purpose: Detect chronic capacity pressure before it becomes a breach.
WITH daily_flags AS (
    SELECT ward_id, ward_name, report_date,
           avg_occupancy_percent,
           CASE WHEN avg_occupancy_percent >= 70 THEN 1 ELSE 0 END AS above_70,
           ROW_NUMBER() OVER (PARTITION BY ward_id ORDER BY report_date)
           - ROW_NUMBER() OVER (PARTITION BY ward_id, 
               CASE WHEN avg_occupancy_percent >= 70 THEN 1 ELSE 0 END
               ORDER BY report_date) AS grp
    FROM ward_occupancy_daily
),
streaks AS (
    SELECT ward_name, grp, 
           COUNT(*) AS consecutive_days,
           MIN(report_date) AS streak_start,
           MAX(report_date) AS streak_end,
           ROUND(AVG(avg_occupancy_percent), 1) AS avg_occ
    FROM daily_flags WHERE above_70 = 1
    GROUP BY ward_name, grp
)
SELECT ward_name, consecutive_days, streak_start, streak_end, avg_occ
FROM streaks WHERE consecutive_days >= 3
ORDER BY consecutive_days DESC;


-- ─── WINDOW FUNCTION QUERIES ───────────────────────────────────────────────

-- Q10: Rank wards by occupancy volatility (std dev) over 30 days.
-- Purpose: High volatility = harder to staff, may need flex beds.
SELECT ward_name,
       ROUND(AVG(avg_occupancy_percent), 1) AS mean_occ,
       ROUND(
           SQRT(AVG(avg_occupancy_percent * avg_occupancy_percent) 
           - AVG(avg_occupancy_percent) * AVG(avg_occupancy_percent))
       , 2) AS std_dev_occ,
       RANK() OVER (ORDER BY 
           SQRT(AVG(avg_occupancy_percent * avg_occupancy_percent)
           - AVG(avg_occupancy_percent) * AVG(avg_occupancy_percent)) DESC
       ) AS volatility_rank
FROM ward_occupancy_daily
WHERE report_date >= DATE('now', '-30 days')
GROUP BY ward_name;


-- Q11: Running 3-day average occupancy per ward with trend.
-- Purpose: Smooth out daily noise and identify real trends.
SELECT ward_name, report_date, avg_occupancy_percent,
       ROUND(AVG(avg_occupancy_percent) OVER (
           PARTITION BY ward_id ORDER BY report_date
           ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
       ), 1) AS moving_avg_3d,
       ROUND(avg_occupancy_percent - LAG(avg_occupancy_percent) OVER (
           PARTITION BY ward_id ORDER BY report_date
       ), 1) AS day_over_day_change
FROM ward_occupancy_daily
ORDER BY ward_name, report_date;


-- Q12: Percentile ranking of each ward's daily peak occupancy.
-- Purpose: Understand distribution — is today's peak unusual or typical?
SELECT ward_name, report_date, peak_occupancy_percent,
       ROUND(PERCENT_RANK() OVER (
           PARTITION BY ward_id ORDER BY peak_occupancy_percent
       ) * 100, 1) AS percentile_rank,
       NTILE(4) OVER (
           PARTITION BY ward_id ORDER BY peak_occupancy_percent
       ) AS quartile
FROM ward_occupancy_daily
ORDER BY ward_name, report_date DESC;


-- ─── TREND & COMPARISON QUERIES ────────────────────────────────────────────

-- Q13: Week-over-week peak occupancy comparison.
-- Purpose: Spot improving or worsening trends.
WITH weekly AS (
    SELECT ward_name,
           strftime('%W', report_date) AS week_num,
           ROUND(MAX(peak_occupancy_percent), 1) AS weekly_peak,
           ROUND(AVG(avg_occupancy_percent), 1) AS weekly_avg,
           SUM(sla_breach_hours) AS breach_hours
    FROM ward_occupancy_daily
    GROUP BY ward_name, strftime('%W', report_date)
)
SELECT w1.ward_name, w1.week_num AS current_week,
       w1.weekly_peak AS this_week_peak,
       w2.weekly_peak AS last_week_peak,
       ROUND(w1.weekly_peak - COALESCE(w2.weekly_peak, w1.weekly_peak), 1) AS peak_change,
       w1.breach_hours AS this_week_breaches,
       COALESCE(w2.breach_hours, 0) AS last_week_breaches
FROM weekly w1
LEFT JOIN weekly w2 
    ON w1.ward_name = w2.ward_name 
    AND CAST(w1.week_num AS INTEGER) = CAST(w2.week_num AS INTEGER) + 1
ORDER BY w1.ward_name, w1.week_num DESC;


-- Q14: LLM explanation effectiveness — which explanations had high confidence?
-- Purpose: Evaluate LLM contribution to clinical decision support.
SELECT ward_name, confidence,
       COUNT(*) AS explanation_count,
       ROUND(AVG(CASE WHEN is_fallback THEN 0 ELSE 1 END) * 100, 1) AS llm_success_rate_pct,
       ROUND(AVG(latency_ms), 0) AS avg_latency_ms,
       ROUND(AVG(tokens_used), 0) AS avg_tokens
FROM llm_explanations
GROUP BY ward_name, confidence
ORDER BY ward_name, confidence;


-- Q15: Correlation between admission priority and occupancy breaches.
-- Purpose: Determine if emergency surges or elective scheduling causes breaches.
-- (This query works best with event-level data joined to breach periods)
SELECT b.ward_name,
       b.status,
       ROUND(b.peak_occupancy_percent, 1) AS peak_occ,
       b.consecutive_hours,
       b.llm_confidence,
       CASE 
           WHEN b.peak_occupancy_percent >= 95 THEN 'Critical (>95%)'
           WHEN b.peak_occupancy_percent >= 90 THEN 'Severe (90-95%)'
           ELSE 'Moderate (85-90%)'
       END AS severity_tier,
       CASE 
           WHEN b.consecutive_hours >= 6 THEN 'Extended (6+ hours)'
           WHEN b.consecutive_hours >= 3 THEN 'Prolonged (3-6 hours)'
           ELSE 'Brief (<3 hours)'
       END AS duration_tier
FROM sla_breaches b
ORDER BY b.peak_occupancy_percent DESC;
