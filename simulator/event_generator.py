"""
HL7-Style ADT Event Generator

Generates realistic patient admission, transfer, and discharge events
with time-of-day and day-of-week patterns, configurable spike/outbreak modes.
"""

import json
import random
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .config import (
    SimulatorConfig,
    WardConfig,
    HOUR_MULTIPLIERS,
    DAY_MULTIPLIERS,
    AGE_GROUPS,
    AGE_GROUP_WEIGHTS,
    PRIORITIES,
    PRIORITY_WEIGHTS,
)

logger = logging.getLogger("simulator.event_generator")


class PatientTracker:
    """
    Tracks patients currently admitted to each ward and bed.
    Needed to generate realistic discharge and transfer events.
    """

    def __init__(self, config: SimulatorConfig):
        self.config = config
        # ward_id -> {bed_id: {patient_id, admit_time, diagnosis}}
        self.ward_occupancy: Dict[str, Dict[str, dict]] = {}
        # patient_id -> ward_id (quick lookup)
        self.patient_location: Dict[str, str] = {}
        # Initialize empty bed maps
        for ward in config.wards:
            self.ward_occupancy[ward.ward_id] = {}

    def get_occupancy(self, ward_id: str) -> int:
        """Current count of occupied beds in a ward."""
        return len(self.ward_occupancy.get(ward_id, {}))

    def get_occupancy_percent(self, ward_id: str) -> float:
        """Current occupancy percentage for a ward."""
        ward = self.config.get_ward(ward_id)
        if not ward:
            return 0.0
        return (self.get_occupancy(ward_id) / ward.total_beds) * 100

    def get_available_bed(self, ward_id: str) -> Optional[str]:
        """Get a random available bed in the ward. Returns None if full."""
        ward = self.config.get_ward(ward_id)
        if not ward:
            return None
        occupied_beds = set(self.ward_occupancy[ward_id].keys())
        all_beds = {f"B-{ward_id[-3:]}-{str(i).zfill(3)}" for i in range(1, ward.total_beds + 1)}
        available = list(all_beds - occupied_beds)
        return random.choice(available) if available else None

    def admit_patient(self, patient_id: str, ward_id: str, bed_id: str, diagnosis: str, timestamp: datetime):
        """Record a patient admission."""
        self.ward_occupancy[ward_id][bed_id] = {
            "patient_id": patient_id,
            "admit_time": timestamp,
            "diagnosis": diagnosis,
        }
        self.patient_location[patient_id] = ward_id

    def discharge_patient(self, ward_id: str) -> Optional[Tuple[str, str]]:
        """Discharge a random patient from a ward. Returns (patient_id, bed_id) or None."""
        beds = self.ward_occupancy.get(ward_id, {})
        if not beds:
            return None
        bed_id = random.choice(list(beds.keys()))
        patient_info = beds.pop(bed_id)
        patient_id = patient_info["patient_id"]
        self.patient_location.pop(patient_id, None)
        return patient_id, bed_id

    def transfer_patient(self, from_ward: str, to_ward: str) -> Optional[Tuple[str, str, str, str]]:
        """
        Transfer a patient from one ward to another.
        Returns (patient_id, old_bed, new_bed, from_ward) or None.
        """
        # Find a patient to transfer
        from_beds = self.ward_occupancy.get(from_ward, {})
        if not from_beds:
            return None
        # Find an available bed in target ward
        new_bed = self.get_available_bed(to_ward)
        if not new_bed:
            return None
        # Pick a patient
        old_bed = random.choice(list(from_beds.keys()))
        patient_info = from_beds.pop(old_bed)
        patient_id = patient_info["patient_id"]
        # Move to new ward
        self.ward_occupancy[to_ward][new_bed] = patient_info
        self.patient_location[patient_id] = to_ward
        return patient_id, old_bed, new_bed, from_ward

    def get_all_occupancy(self) -> Dict[str, dict]:
        """Get occupancy info for all wards."""
        result = {}
        for ward in self.config.wards:
            occ = self.get_occupancy(ward.ward_id)
            result[ward.ward_id] = {
                "ward_name": ward.ward_name,
                "occupied": occ,
                "total": ward.total_beds,
                "percent": round((occ / ward.total_beds) * 100, 1),
            }
        return result


class HL7EventGenerator:
    """
    Generates realistic HL7-style ADT events with time-based patterns.
    """

    def __init__(self, config: SimulatorConfig):
        self.config = config
        self.tracker = PatientTracker(config)
        self._patient_counter = 0
        # Track spikes
        self._active_spikes: Dict[str, datetime] = {}  # ward_id -> spike_end_time

    def _generate_patient_id(self) -> str:
        """Generate sequential patient ID."""
        self._patient_counter += 1
        return f"P-{str(self._patient_counter).zfill(6)}"

    def _get_admission_rate(self, ward: WardConfig, current_time: datetime) -> float:
        """
        Calculate the admission rate for a ward at a given time,
        applying time-of-day and day-of-week multipliers.
        """
        hour = current_time.hour
        day = current_time.weekday()

        base_rate = (ward.normal_admission_rate_min + ward.normal_admission_rate_max) / 2.0

        # Check if this ward is in spike mode
        is_spiking = (
            ward.ward_id in self._active_spikes
            and current_time < self._active_spikes[ward.ward_id]
        )
        if is_spiking:
            base_rate = (ward.spike_admission_rate_min + ward.spike_admission_rate_max) / 2.0

        # Check outbreak mode
        if self.config.outbreak_mode and ward.ward_id == self.config.outbreak_ward_id:
            base_rate = (
                (ward.spike_admission_rate_min + ward.spike_admission_rate_max) / 2.0
                * self.config.outbreak_intensity
            )

        # Apply multipliers
        rate = base_rate * HOUR_MULTIPLIERS.get(hour, 1.0) * DAY_MULTIPLIERS.get(day, 1.0)
        return max(0.1, rate)  # Minimum floor

    def _should_spike(self, ward: WardConfig, current_time: datetime) -> bool:
        """Determine if a random spike should occur for this ward."""
        if ward.ward_id in self._active_spikes and current_time < self._active_spikes[ward.ward_id]:
            return False  # Already spiking
        if self.config.spike_ward_id and ward.ward_id != self.config.spike_ward_id:
            return False  # Specific ward targeting
        return random.random() < self.config.spike_probability

    def _decide_event_type(self, ward: WardConfig, current_time: datetime) -> str:
        """
        Decide what type of event to generate based on current ward state.
        Logic:
        - If ward is >90% full, higher chance of discharge
        - If ward is <30% full, higher chance of admit
        - Transfers are always relatively rare
        """
        occupancy_pct = self.tracker.get_occupancy_percent(ward.ward_id)

        if occupancy_pct >= 95:
            # Almost full: heavy discharge bias
            weights = {"ADT_A01": 0.1, "ADT_A02": 0.1, "ADT_A03": 0.8}
        elif occupancy_pct >= 85:
            # High occupancy: moderate discharge bias
            weights = {"ADT_A01": 0.25, "ADT_A02": 0.1, "ADT_A03": 0.65}
        elif occupancy_pct >= 50:
            # Normal: balanced but more admits
            weights = {"ADT_A01": 0.5, "ADT_A02": 0.1, "ADT_A03": 0.4}
        elif occupancy_pct >= 20:
            # Low-ish: more admits
            weights = {"ADT_A01": 0.65, "ADT_A02": 0.1, "ADT_A03": 0.25}
        else:
            # Very low: heavy admit bias
            weights = {"ADT_A01": 0.8, "ADT_A02": 0.05, "ADT_A03": 0.15}

        event_types = list(weights.keys())
        probs = list(weights.values())
        return random.choices(event_types, weights=probs, k=1)[0]

    def _select_age_group(self, ward: WardConfig) -> str:
        """Select age group based on ward type."""
        if ward.ward_name == "Pediatrics":
            return "pediatric"
        weights = list(AGE_GROUP_WEIGHTS.values())
        return random.choices(AGE_GROUPS, weights=weights, k=1)[0]

    def _select_priority(self, ward: WardConfig) -> str:
        """Select admission priority."""
        if ward.ward_name == "Emergency":
            # Emergency ward has much higher emergency admissions
            weights = [0.7, 0.1, 0.2]
        else:
            weights = list(PRIORITY_WEIGHTS.values())
        return random.choices(PRIORITIES, weights=weights, k=1)[0]

    def generate_event(self, current_time: datetime) -> Optional[dict]:
        """
        Generate a single HL7-style ADT event.
        Returns event dict or None if no event should be generated.
        """
        # Pick a random ward, weighted by admission rate
        rates = []
        for ward in self.config.wards:
            rates.append(self._get_admission_rate(ward, current_time))

        total_rate = sum(rates)
        ward_probs = [r / total_rate for r in rates]
        ward = random.choices(self.config.wards, weights=ward_probs, k=1)[0]

        # Check for random spike
        if self._should_spike(ward, current_time):
            spike_duration = random.randint(1, 4)  # 1-4 hours
            self._active_spikes[ward.ward_id] = current_time + timedelta(hours=spike_duration)
            logger.info(f"⚡ SPIKE activated on {ward.ward_name} for {spike_duration}h")

        # Decide event type
        event_type = self._decide_event_type(ward, current_time)

        # Build the event
        event = {
            "message_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": current_time.isoformat(),
            "ward_id": ward.ward_id,
            "ward_name": ward.ward_name,
        }

        if event_type == "ADT_A01":
            # ADMISSION
            bed = self.tracker.get_available_bed(ward.ward_id)
            if bed is None:
                # Ward is full — cannot admit, try discharge instead
                result = self.tracker.discharge_patient(ward.ward_id)
                if result:
                    patient_id, bed_id = result
                    event["event_type"] = "ADT_A03"
                    event["patient_id"] = patient_id
                    event["bed_id"] = bed_id
                    event["diagnosis_category"] = random.choice(ward.diagnosis_categories)
                    event["age_group"] = self._select_age_group(ward)
                    event["priority"] = self._select_priority(ward)
                    return event
                return None  # Can't do anything

            patient_id = self._generate_patient_id()
            diagnosis = random.choice(ward.diagnosis_categories)
            self.tracker.admit_patient(patient_id, ward.ward_id, bed, diagnosis, current_time)

            event["patient_id"] = patient_id
            event["bed_id"] = bed
            event["diagnosis_category"] = diagnosis
            event["age_group"] = self._select_age_group(ward)
            event["priority"] = self._select_priority(ward)

        elif event_type == "ADT_A03":
            # DISCHARGE
            result = self.tracker.discharge_patient(ward.ward_id)
            if result is None:
                # No patients to discharge — generate an admission instead
                bed = self.tracker.get_available_bed(ward.ward_id)
                if bed:
                    patient_id = self._generate_patient_id()
                    diagnosis = random.choice(ward.diagnosis_categories)
                    self.tracker.admit_patient(patient_id, ward.ward_id, bed, diagnosis, current_time)
                    event["event_type"] = "ADT_A01"
                    event["patient_id"] = patient_id
                    event["bed_id"] = bed
                    event["diagnosis_category"] = diagnosis
                    event["age_group"] = self._select_age_group(ward)
                    event["priority"] = self._select_priority(ward)
                else:
                    return None
            else:
                patient_id, bed_id = result
                event["patient_id"] = patient_id
                event["bed_id"] = bed_id
                event["diagnosis_category"] = random.choice(ward.diagnosis_categories)
                event["age_group"] = self._select_age_group(ward)
                event["priority"] = self._select_priority(ward)

        elif event_type == "ADT_A02":
            # TRANSFER
            other_wards = [w for w in self.config.wards if w.ward_id != ward.ward_id]
            if not other_wards:
                return None
            target_ward = random.choice(other_wards)
            result = self.tracker.transfer_patient(ward.ward_id, target_ward.ward_id)
            if result is None:
                return None
            patient_id, old_bed, new_bed, from_ward = result
            event["patient_id"] = patient_id
            event["bed_id"] = new_bed
            event["transfer_from_ward"] = from_ward
            event["transfer_from_bed"] = old_bed
            event["ward_id"] = target_ward.ward_id
            event["ward_name"] = target_ward.ward_name
            event["diagnosis_category"] = random.choice(target_ward.diagnosis_categories)
            event["age_group"] = self._select_age_group(target_ward)
            event["priority"] = "transfer"

        # Validate: ensure no nulls in critical fields
        critical_fields = ["message_id", "event_type", "patient_id", "ward_id", "timestamp", "bed_id"]
        for field in critical_fields:
            if field not in event or event[field] is None:
                logger.warning(f"Dropping event with null critical field: {field}")
                return None

        return event

    def generate_batch(self, current_time: datetime, count: int = 10) -> List[dict]:
        """Generate a batch of events around a given timestamp."""
        events = []
        for i in range(count):
            # Add small random offset to each event timestamp
            offset = timedelta(seconds=random.uniform(0, 60 / max(count, 1)))
            event_time = current_time + offset
            event = self.generate_event(event_time)
            if event:
                events.append(event)
        return events

    def pre_populate(self, base_time: datetime, target_occupancy_pct: float = 60.0):
        """
        Pre-populate wards with patients to reach a target occupancy.
        Call this before starting simulation to avoid starting from empty.
        """
        logger.info(f"Pre-populating wards to ~{target_occupancy_pct}% occupancy...")
        for ward in self.config.wards:
            target_count = int(ward.total_beds * (target_occupancy_pct / 100))
            for i in range(target_count):
                bed = self.tracker.get_available_bed(ward.ward_id)
                if bed:
                    patient_id = self._generate_patient_id()
                    diagnosis = random.choice(ward.diagnosis_categories)
                    # Vary admission times in the past
                    admit_time = base_time - timedelta(
                        hours=random.uniform(1, ward.avg_length_of_stay_hours)
                    )
                    self.tracker.admit_patient(patient_id, ward.ward_id, bed, diagnosis, admit_time)

        # Log the initial state
        for ward_id, info in self.tracker.get_all_occupancy().items():
            logger.info(f"  {info['ward_name']}: {info['occupied']}/{info['total']} ({info['percent']}%)")

    def get_occupancy_snapshot(self) -> Dict[str, dict]:
        """Get current occupancy for all wards."""
        return self.tracker.get_all_occupancy()
