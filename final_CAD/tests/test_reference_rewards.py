import csv
import math
import os
import sys
from pathlib import Path

CAD_DIR = Path(__file__).parents[1]
REFERENCE_CSV = CAD_DIR / "references.csv"
sys.path.insert(0, str(CAD_DIR))

from circuit_env import CircuitEnv

def test_reference_design_rewards():
    with REFERENCE_CSV.open(newline="") as reference_file:
        rows = {
            row["Attribute"]: row
            for row in csv.DictReader(reference_file)
        }

    original_cwd = Path.cwd()
    try:
        os.chdir(CAD_DIR)
        env = CircuitEnv(run_id="reference_reward_test")

        for design_index in range(1, 6):
            design = f"Design {design_index}"
            norm_specs = {
                spec: float(rows[f"norm_{spec}"][design])
                for spec in env.dict_targets
            }

            reward, hard_satisfied = env.reward_computation(norm_specs)
            print(f"{design}: reward={reward}, hard_satisfied={hard_satisfied}, expected_reward={rows['reward'][design]}, expected_hard_satisfied=False")
            expected_reward = float(rows["reward"][design])
            assert math.isclose(reward, expected_reward, abs_tol=1e-9), (
                f"{design}: expected reward {expected_reward}, got {reward}"
            )
            assert hard_satisfied is False, (
                f"{design}: expected hard_satisfied=False, got {hard_satisfied}"
            )
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    test_reference_design_rewards()
    print("All five reference design reward checks passed.")