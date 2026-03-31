"""
Kafka Producer for HL7 Events

Publishes generated HL7-style ADT events to Kafka.
Supports both real-time streaming and batch mode for testing.
"""

import json
import time
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Optional

try:
    from confluent_kafka import Producer
    HAS_CONFLUENT = True
except ImportError:
    HAS_CONFLUENT = False

from .config import SimulatorConfig
from .event_generator import HL7EventGenerator

logger = logging.getLogger("simulator.kafka_producer")


class KafkaEventProducer:
    """Publishes HL7 events to Kafka topic."""

    def __init__(self, config: SimulatorConfig):
        self.config = config
        self.generator = HL7EventGenerator(config)
        self.producer: Optional[object] = None
        self._running = False
        self._event_count = 0

        if HAS_CONFLUENT:
            self.producer = Producer({
                "bootstrap.servers": config.kafka_bootstrap_servers,
                "client.id": "hospital-simulator",
                "acks": "all",
                "retries": 3,
                "retry.backoff.ms": 1000,
            })
        else:
            logger.warning("confluent_kafka not installed — running in file-only mode")

    def _delivery_callback(self, err, msg):
        """Kafka delivery report callback."""
        if err:
            logger.error(f"Message delivery failed: {err}")
        else:
            if self.config.log_events and self._event_count % 50 == 0:
                logger.debug(f"Delivered to {msg.topic()} [{msg.partition()}] @ {msg.offset()}")

    def publish_event(self, event: dict) -> bool:
        """Publish a single event to Kafka."""
        try:
            event_json = json.dumps(event)
            if self.producer:
                self.producer.produce(
                    topic=self.config.kafka_raw_topic,
                    key=event.get("ward_id", "unknown"),
                    value=event_json.encode("utf-8"),
                    callback=self._delivery_callback,
                )
                self.producer.poll(0)
            self._event_count += 1
            return True
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False

    def publish_alert(self, alert: dict) -> bool:
        """Publish an alert to the alerts Kafka topic."""
        try:
            alert_json = json.dumps(alert)
            if self.producer:
                self.producer.produce(
                    topic=self.config.kafka_alerts_topic,
                    key=alert.get("ward_id", "unknown"),
                    value=alert_json.encode("utf-8"),
                    callback=self._delivery_callback,
                )
                self.producer.poll(0)
            return True
        except Exception as e:
            logger.error(f"Failed to publish alert: {e}")
            return False

    def run_realtime(self, duration_minutes: int = 30, pre_populate: bool = True):
        """
        Run the simulator in real-time mode.
        Generates events continuously based on configured rates.
        """
        self._running = True
        start_time = datetime.now()
        current_time = start_time

        # Set up graceful shutdown
        def signal_handler(sig, frame):
            logger.info("\n🛑 Shutting down simulator...")
            self._running = False

        signal.signal(signal.SIGINT, signal_handler)

        # Pre-populate wards
        if pre_populate:
            self.generator.pre_populate(current_time, target_occupancy_pct=60.0)

        logger.info(f"🏥 Starting real-time simulation for {duration_minutes} minutes")
        logger.info(f"   Speed: {self.config.speed_multiplier}x | Events/sec: {self.config.events_per_second}")
        logger.info(f"   Outbreak mode: {'ON ⚠️' if self.config.outbreak_mode else 'OFF'}")
        logger.info(f"   Kafka: {'Connected' if self.producer else 'File-only mode'}")
        logger.info("─" * 60)

        end_time = start_time + timedelta(minutes=duration_minutes)
        interval = 1.0 / self.config.events_per_second

        while self._running and current_time < end_time:
            # Generate event at current simulated time
            event = self.generator.generate_event(current_time)

            if event:
                self.publish_event(event)

                if self.config.log_events:
                    occ = self.generator.tracker.get_occupancy_percent(event["ward_id"])
                    status = "🟢" if occ < 70 else "🟡" if occ < 85 else "🟠" if occ < 95 else "🔴"
                    logger.info(
                        f"{status} [{event['event_type']}] {event['ward_name']:12s} | "
                        f"Patient: {event['patient_id']} | Bed: {event['bed_id']} | "
                        f"Occupancy: {occ:.0f}%"
                    )

                    # Check for SLA breach
                    if occ >= 85:
                        ward_config = self.config.get_ward(event["ward_id"])
                        alert = {
                            "alert_type": "occupancy_warning" if occ < 95 else "occupancy_critical",
                            "ward_id": event["ward_id"],
                            "ward_name": event["ward_name"],
                            "occupancy_percent": occ,
                            "total_beds": ward_config.total_beds if ward_config else 0,
                            "occupied_beds": self.generator.tracker.get_occupancy(event["ward_id"]),
                            "timestamp": current_time.isoformat(),
                        }
                        self.publish_alert(alert)

            # Advance time
            time_step = interval * self.config.speed_multiplier
            current_time += timedelta(seconds=time_step * 60)  # Scale to simulate faster
            time.sleep(interval)

        # Flush remaining messages
        if self.producer:
            self.producer.flush(timeout=10)

        logger.info("─" * 60)
        logger.info(f"✅ Simulation complete. Total events: {self._event_count}")
        self._print_summary()

    def run_batch(self, hours: int = 24, events_per_hour: int = 50) -> list:
        """
        Generate a batch of events for a given number of hours.
        Useful for testing and seeding historical data.
        Returns list of all generated events.
        """
        all_events = []
        base_time = datetime.now() - timedelta(hours=hours)

        # Pre-populate
        self.generator.pre_populate(base_time, target_occupancy_pct=55.0)

        logger.info(f"📦 Generating batch: {hours} hours × {events_per_hour} events/hr")

        for hour in range(hours):
            current_hour = base_time + timedelta(hours=hour)
            events = self.generator.generate_batch(current_hour, count=events_per_hour)
            for event in events:
                self.publish_event(event)
                all_events.append(event)

            occ_snapshot = self.generator.get_occupancy_snapshot()
            max_ward = max(occ_snapshot.items(), key=lambda x: x[1]["percent"])
            logger.info(
                f"  Hour {hour:3d}: {len(events):3d} events | "
                f"Peak: {max_ward[1]['ward_name']} at {max_ward[1]['percent']}%"
            )

        if self.producer:
            self.producer.flush(timeout=10)

        logger.info(f"✅ Batch complete. Total: {len(all_events)} events")
        return all_events

    def save_events_to_file(self, events: list, filepath: str):
        """Save events to a JSON file for reference/testing."""
        with open(filepath, "w") as f:
            json.dump(events, f, indent=2, default=str)
        logger.info(f"💾 Saved {len(events)} events to {filepath}")

    def _print_summary(self):
        """Print final occupancy summary."""
        logger.info("\n📊 Final Ward Occupancy:")
        for ward_id, info in self.generator.get_occupancy_snapshot().items():
            bar_len = int(info["percent"] / 2)
            bar = "█" * bar_len + "░" * (50 - bar_len)
            status = "🟢" if info["percent"] < 70 else "🟡" if info["percent"] < 85 else "🟠" if info["percent"] < 95 else "🔴"
            logger.info(
                f"  {status} {info['ward_name']:12s} |{bar}| "
                f"{info['occupied']:3d}/{info['total']:3d} ({info['percent']:5.1f}%)"
            )
