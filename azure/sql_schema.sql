-- ═══════════════════════════════════════════════════════════════════════════
-- Azure SQL Schema — Hospital Bed Occupancy Monitor
-- Run this in Azure SQL Database after creation
-- ═══════════════════════════════════════════════════════════════════════════

-- Ward Configuration
CREATE TABLE wards (
    ward_id NVARCHAR(10) PRIMARY KEY,
    ward_name NVARCHAR(50) NOT NULL,
    total_beds INT NOT NULL,
    created_at DATETIME2 DEFAULT GETDATE()
);

INSERT INTO wards (ward_id, ward_name, total_beds) VALUES
('W-001', 'ICU East', 20),
('W-002', 'ICU West', 20),
('W-003', 'General A', 40),
('W-004', 'General B', 40),
('W-005', 'Pediatrics', 25),
('W-006', 'Emergency', 30),
('W-007', 'Oncology', 15);

-- Hourly Occupancy Snapshots
CREATE TABLE ward_occupancy_hourly (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ward_id NVARCHAR(10) NOT NULL,
    ward_name NVARCHAR(50) NOT NULL,
    snapshot_hour DATETIME2 NOT NULL,
    occupied_beds INT NOT NULL,
    total_beds INT NOT NULL,
    occupancy_percent DECIMAL(5,1) NOT NULL,
    admits_count INT DEFAULT 0,
    discharges_count INT DEFAULT 0,
    transfers_in INT DEFAULT 0,
    transfers_out INT DEFAULT 0,
    created_at DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT uq_ward_hour UNIQUE (ward_id, snapshot_hour)
);

CREATE INDEX idx_occ_hourly_ward_time ON ward_occupancy_hourly(ward_id, snapshot_hour);
CREATE INDEX idx_occ_hourly_time ON ward_occupancy_hourly(snapshot_hour);

-- Daily Summaries
CREATE TABLE ward_occupancy_daily (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ward_id NVARCHAR(10) NOT NULL,
    ward_name NVARCHAR(50) NOT NULL,
    report_date DATE NOT NULL,
    avg_occupancy_percent DECIMAL(5,1),
    peak_occupancy_percent DECIMAL(5,1),
    peak_occupancy_hour INT,
    min_occupancy_percent DECIMAL(5,1),
    total_admits INT DEFAULT 0,
    total_discharges INT DEFAULT 0,
    sla_breach_hours INT DEFAULT 0,
    created_at DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT uq_ward_date UNIQUE (ward_id, report_date)
);

-- SLA Breaches
CREATE TABLE sla_breaches (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ward_id NVARCHAR(10) NOT NULL,
    ward_name NVARCHAR(50) NOT NULL,
    breach_start_time DATETIME2 NOT NULL,
    breach_end_time DATETIME2,
    consecutive_hours DECIMAL(5,1) DEFAULT 0,
    peak_occupancy_percent DECIMAL(5,1),
    current_occupancy_percent DECIMAL(5,1),
    status NVARCHAR(20) DEFAULT 'active',
    llm_explanation NVARCHAR(MAX),
    llm_confidence NVARCHAR(20),
    resolution_note NVARCHAR(500),
    created_at DATETIME2 DEFAULT GETDATE(),
    resolved_at DATETIME2
);

CREATE INDEX idx_breach_ward_status ON sla_breaches(ward_id, status);

-- Anomaly Flags
CREATE TABLE anomaly_flags (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ward_id NVARCHAR(10) NOT NULL,
    ward_name NVARCHAR(50) NOT NULL,
    detection_time DATETIME2 NOT NULL,
    hour_of_day INT NOT NULL,
    z_score DECIMAL(8,3) NOT NULL,
    is_anomaly BIT NOT NULL DEFAULT 0,
    baseline_mean DECIMAL(8,2) NOT NULL,
    baseline_std DECIMAL(8,2) NOT NULL,
    current_count INT NOT NULL,
    threshold_used DECIMAL(4,1) DEFAULT 2.5,
    created_at DATETIME2 DEFAULT GETDATE()
);

CREATE INDEX idx_anomaly_ward_time ON anomaly_flags(ward_id, detection_time);

-- LLM Explanations
CREATE TABLE llm_explanations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    breach_id INT REFERENCES sla_breaches(id),
    ward_id NVARCHAR(10) NOT NULL,
    ward_name NVARCHAR(50) NOT NULL,
    context_json NVARCHAR(MAX),
    explanation NVARCHAR(MAX) NOT NULL,
    confidence NVARCHAR(20) DEFAULT 'medium',
    model_used NVARCHAR(50) DEFAULT 'claude-sonnet',
    is_fallback BIT DEFAULT 0,
    tokens_used INT DEFAULT 0,
    latency_ms INT DEFAULT 0,
    created_at DATETIME2 DEFAULT GETDATE()
);

-- ═══════════════════════════════════════════════════════════════════════════
-- Stored Procedure: Daily Summary Computation
-- ═══════════════════════════════════════════════════════════════════════════
GO
CREATE PROCEDURE sp_compute_daily_summary
    @report_date DATE
AS
BEGIN
    MERGE ward_occupancy_daily AS target
    USING (
        SELECT
            ward_id, ward_name, CAST(snapshot_hour AS DATE) AS report_date,
            ROUND(AVG(occupancy_percent), 1) AS avg_occ,
            ROUND(MAX(occupancy_percent), 1) AS peak_occ,
            ROUND(MIN(occupancy_percent), 1) AS min_occ,
            SUM(admits_count) AS total_admits,
            SUM(discharges_count) AS total_discharges,
            SUM(CASE WHEN occupancy_percent >= 85 THEN 1 ELSE 0 END) AS breach_hrs
        FROM ward_occupancy_hourly
        WHERE CAST(snapshot_hour AS DATE) = @report_date
        GROUP BY ward_id, ward_name, CAST(snapshot_hour AS DATE)
    ) AS source
    ON target.ward_id = source.ward_id AND target.report_date = source.report_date
    WHEN MATCHED THEN UPDATE SET
        avg_occupancy_percent = source.avg_occ,
        peak_occupancy_percent = source.peak_occ,
        min_occupancy_percent = source.min_occ,
        total_admits = source.total_admits,
        total_discharges = source.total_discharges,
        sla_breach_hours = source.breach_hrs
    WHEN NOT MATCHED THEN INSERT
        (ward_id, ward_name, report_date, avg_occupancy_percent,
         peak_occupancy_percent, min_occupancy_percent,
         total_admits, total_discharges, sla_breach_hours)
    VALUES (source.ward_id, source.ward_name, source.report_date,
            source.avg_occ, source.peak_occ, source.min_occ,
            source.total_admits, source.total_discharges, source.breach_hrs);
END
GO
