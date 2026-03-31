"""
Main entry point for running the HL7 event simulator.

Usage:
  python -m simulator.run_simulator --mode realtime --duration 30
  python -m simulator.run_simulator --mode batch --hours 168 --events-per-hour 60
  python -m simulator.run_simulator --mode realtime --outbreak --outbreak-ward W-006
"""

import argparse
import logging
import os
import sys

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.config import SimulatorConfig
from simulator.kafka_producer import KafkaEventProducer

# ─── Logging Setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-28s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("simulator")


def main():
    parser = argparse.ArgumentParser(
        description="Healthcare HL7 ADT Event Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Real-time mode (30-minute normal day):
    python -m simulator.run_simulator --mode realtime --duration 30

  Real-time with outbreak spike on Emergency:
    python -m simulator.run_simulator --mode realtime --duration 30 --outbreak --outbreak-ward W-006

  Batch mode (7 days of historical data):
    python -m simulator.run_simulator --mode batch --hours 168 --events-per-hour 60

  Fast batch (save to file for Spark testing):
    python -m simulator.run_simulator --mode batch --hours 24 --output ./data/test_events.json
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["realtime", "batch"],
        default="realtime",
        help="Simulation mode: 'realtime' for live Kafka streaming, 'batch' for bulk generation",
    )
    parser.add_argument("--duration", type=int, default=30, help="Duration in minutes (realtime mode)")
    parser.add_argument("--hours", type=int, default=24, help="Hours of data to generate (batch mode)")
    parser.add_argument("--events-per-hour", type=int, default=50, help="Events per hour (batch mode)")
    parser.add_argument("--speed", type=float, default=1.0, help="Speed multiplier (1.0 = realtime)")
    parser.add_argument("--eps", type=float, default=5.0, help="Events per second")
    parser.add_argument("--spike-prob", type=float, default=0.10, help="Spike probability per ward per hour")
    parser.add_argument("--outbreak", action="store_true", help="Enable outbreak injection mode")
    parser.add_argument("--outbreak-ward", type=str, default="W-006", help="Ward to spike during outbreak")
    parser.add_argument("--outbreak-intensity", type=float, default=2.0, help="Outbreak intensity multiplier")
    parser.add_argument("--kafka", type=str, default="localhost:9092", help="Kafka bootstrap servers")
    parser.add_argument("--output", type=str, default=None, help="Save events to JSON file")
    parser.add_argument("--no-kafka", action="store_true", help="Run without Kafka (file output only)")
    parser.add_argument("--quiet", action="store_true", help="Reduce logging verbosity")

    args = parser.parse_args()

    # Build config
    config = SimulatorConfig(
        speed_multiplier=args.speed,
        events_per_second=args.eps,
        spike_probability=args.spike_prob,
        outbreak_mode=args.outbreak,
        outbreak_ward_id=args.outbreak_ward,
        outbreak_intensity=args.outbreak_intensity,
        kafka_bootstrap_servers=args.kafka if not args.no_kafka else "none",
        log_events=not args.quiet,
    )
    config.load_wards()

    logger.info("=" * 60)
    logger.info("🏥 Healthcare Patient Flow & Bed Occupancy Simulator")
    logger.info("=" * 60)
    logger.info(f"  Wards: {len(config.wards)} | Total beds: {config.total_beds}")
    logger.info(f"  Mode: {args.mode} | Speed: {args.speed}x")
    if args.outbreak:
        ward = config.get_ward(args.outbreak_ward)
        logger.info(f"  ⚠️  OUTBREAK MODE: {ward.ward_name if ward else args.outbreak_ward} ({args.outbreak_intensity}x)")
    logger.info("=" * 60)

    # Create producer
    producer = KafkaEventProducer(config)

    if args.mode == "realtime":
        producer.run_realtime(duration_minutes=args.duration)
    elif args.mode == "batch":
        events = producer.run_batch(hours=args.hours, events_per_hour=args.events_per_hour)
        if args.output:
            os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
            producer.save_events_to_file(events, args.output)

    logger.info("🏁 Simulator finished.")


if __name__ == "__main__":
    main()
