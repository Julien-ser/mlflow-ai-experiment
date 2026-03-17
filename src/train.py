"""
Unified training CLI.
"""

import argparse
import yaml
from .training import Trainer


def main():
    parser = argparse.ArgumentParser(description="Unified training pipeline")
    parser.add_argument(
        "--config",
        type=str,
        default="config/training.yaml",
        help="Path to training configuration YAML",
    )
    args = parser.parse_args()

    # Load config from YAML
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    trainer = Trainer(config)
    results = trainer.train()
    print(f"Training completed. Metrics: {results}")


if __name__ == "__main__":
    main()
