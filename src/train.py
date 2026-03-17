"""
Unified training CLI.
"""

import argparse
from .training import TrainingPipeline


def main():
    parser = argparse.ArgumentParser(description="Unified training pipeline")
    parser.add_argument(
        "--config",
        type=str,
        default="config/training.yaml",
        help="Path to training configuration YAML",
    )
    args = parser.parse_args()

    pipeline = TrainingPipeline(args.config)
    results = pipeline.train()
    print(f"Training completed. Run ID: {results.get('run_id')}")


if __name__ == "__main__":
    main()
