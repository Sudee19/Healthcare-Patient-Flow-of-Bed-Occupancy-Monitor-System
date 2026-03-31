"""
Simulator Configuration
Loads ward definitions and provides configurable simulation parameters.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WARD_CONFIG_PATH = os.path.join(BASE_DIR, "config", "wards.json")

# ─── Load ward configuration ─────────────────────────────────────────────────
def load_ward_config(path: str = WARD_CONFIG_PATH) -> dict:
    """Load ward configuration from JSON file."""
    with open(path, "r") as f:
        return json.load(f)


@dataclass
class WardConfig:
    """Configuration for a single ward."""
    ward_id: str
    ward_name: str
    total_beds: int
    normal_admission_rate_min: int
    normal_admission_rate_max: int
    spike_admission_rate_min: int
    spike_admission_rate_max: int
    avg_length_of_stay_hours: int
    diagnosis_categories: List[str]

    @classmethod
    def from_dict(cls, data: dict) -> "WardConfig":
        return cls(
            ward_id=data["ward_id"],
            ward_name=data["ward_name"],
            total_beds=data["total_beds"],
            normal_admission_rate_min=data["normal_admission_rate"]["min"],
            normal_admission_rate_max=data["normal_admission_rate"]["max"],
            spike_admission_rate_min=data["spike_admission_rate"]["min"],
            spike_admission_rate_max=data["spike_admission_rate"]["max"],
            avg_length_of_stay_hours=data["avg_length_of_stay_hours"],
            diagnosis_categories=data["diagnosis_categories"],
        )


@dataclass
class SimulatorConfig:
    """Global simulator configuration."""
    # Speed multiplier: 1.0 = real-time, 10.0 = 10x faster
    speed_multiplier: float = 1.0
    # Events per second (approx)
    events_per_second: float = 5.0
    # Probability of a random spike occurring per ward per hour
    spike_probability: float = 0.10
    # Which ward to spike (None = random)
    spike_ward_id: Optional[str] = None
    # Outbreak injection mode
    outbreak_mode: bool = False
    # Outbreak target ward
    outbreak_ward_id: str = "W-006"  # Emergency by default
    # Outbreak intensity multiplier (applied on top of spike rate)
    outbreak_intensity: float = 2.0
    # Kafka settings
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_raw_topic: str = "hospital_adt_events"
    kafka_alerts_topic: str = "hospital_alerts"
    # Logging
    log_events: bool = True

    # Ward configs (populated on load)
    wards: List[WardConfig] = field(default_factory=list)

    def load_wards(self, path: str = WARD_CONFIG_PATH):
        """Load ward definitions from config file."""
        config = load_ward_config(path)
        self.wards = [WardConfig.from_dict(w) for w in config["wards"]]
        return self

    def get_ward(self, ward_id: str) -> Optional[WardConfig]:
        """Get a specific ward config by ID."""
        for w in self.wards:
            if w.ward_id == ward_id:
                return w
        return None

    @property
    def total_beds(self) -> int:
        return sum(w.total_beds for w in self.wards)

    @property
    def ward_ids(self) -> List[str]:
        return [w.ward_id for w in self.wards]


# ─── Time-of-day admission multipliers ──────────────────────────────────────
# Higher admissions 8-11 AM and 6-10 PM, lower overnight
HOUR_MULTIPLIERS = {
    0: 0.3, 1: 0.2, 2: 0.15, 3: 0.15, 4: 0.2, 5: 0.3,
    6: 0.5, 7: 0.7, 8: 1.2, 9: 1.4, 10: 1.3, 11: 1.1,
    12: 0.9, 13: 0.8, 14: 0.8, 15: 0.9, 16: 1.0, 17: 1.1,
    18: 1.3, 19: 1.4, 20: 1.2, 21: 1.0, 22: 0.7, 23: 0.4,
}

# ─── Day-of-week admission multipliers ──────────────────────────────────────
# Mondays and Fridays are busier
DAY_MULTIPLIERS = {
    0: 1.3,   # Monday
    1: 1.0,   # Tuesday
    2: 0.9,   # Wednesday
    3: 0.95,  # Thursday
    4: 1.2,   # Friday
    5: 0.7,   # Saturday
    6: 0.6,   # Sunday
}

# ─── Event types ─────────────────────────────────────────────────────────────
EVENT_TYPES = {
    "ADT_A01": "admit",
    "ADT_A02": "transfer",
    "ADT_A03": "discharge",
}

# ─── Diagnosis categories (cross-ward) ──────────────────────────────────────
AGE_GROUPS = ["pediatric", "adult", "geriatric"]
PRIORITIES = ["emergency", "elective", "transfer"]

# Age group weights (adult most common)
AGE_GROUP_WEIGHTS = {
    "pediatric": 0.15,
    "adult": 0.55,
    "geriatric": 0.30,
}

# Priority weights
PRIORITY_WEIGHTS = {
    "emergency": 0.35,
    "elective": 0.45,
    "transfer": 0.20,
}
