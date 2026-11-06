"""Print the highest-reward design(s) from a solutions CSV as formatted JSON.

Usage from the repository root:
    python CAD/analysis/best_design.py CAD/solutions/2026-11-05--14-19-04.csv
"""

import argparse
import ast
import csv
import json
import math
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from utils.plotting import plot_pareto_front as draw_pareto_front


REQUIRED_COLUMNS = ("Simulation step", "Specs", "Circuit Params", "Reward")


class NumpyScalarNormalizer(ast.NodeTransformer):
    """Allow the np.float64(...) representation used in saved CSV dictionaries."""

    def visit_Call(self, node):
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "np"
            and node.func.attr == "float64"
            and len(node.args) == 1
            and not node.keywords
        ):
            return self.visit(node.args[0])
        return self.generic_visit(node)


def parse_dictionary(value, column, line_number):
    try:
        expression = ast.parse(value, mode="eval")
        normalized = NumpyScalarNormalizer().visit(expression)
        parsed = ast.literal_eval(normalized)
    except (SyntaxError, TypeError, ValueError) as error:
        raise ValueError(
            f"Invalid {column} dictionary on CSV line {line_number}: {error}"
        ) from error

    if not isinstance(parsed, dict):
        raise ValueError(f"{column} on CSV line {line_number} must be a dictionary")
    return parsed


def find_best_designs(csv_path):
    designs = []
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        missing_columns = set(REQUIRED_COLUMNS) - set(reader.fieldnames or ())
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"CSV is missing required columns: {missing}")

        for row in reader:
            if not any(value and value.strip() for value in row.values() if value is not None):
                continue

            line_number = reader.line_num
            try:
                reward = float(row["Reward"])
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"Invalid Reward on CSV line {line_number}: {row['Reward']!r}"
                ) from error
            if not math.isfinite(reward):
                raise ValueError(f"Reward on CSV line {line_number} must be finite")

            designs.append(
                {
                    "simulation_step": row["Simulation step"],
                    "reward": reward,
                    "specs": parse_dictionary(row["Specs"], "Specs", line_number),
                    "circuit_params": parse_dictionary(
                        row["Circuit Params"], "Circuit Params", line_number
                    ),
                }
            )

    if not designs:
        raise ValueError("CSV contains no design rows")

    max_reward = max(design["reward"] for design in designs)
    best_designs = [
        design for design in designs if design["reward"] == max_reward
    ]
    return max_reward, best_designs, designs


def create_pareto_plot(csv_path, designs):
    solutions = []
    for index, design in enumerate(designs, start=1):
        specs = design["specs"]
        if "area" not in specs or "current" not in specs:
            raise ValueError(
                f"Design {index} in {csv_path} must include 'area' and 'current' "
                "specifications for the Pareto plot"
            )
        try:
            area = float(specs["area"])
            current = float(specs["current"])
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Design {index} in {csv_path} has non-numeric area or current"
            ) from error
        if not math.isfinite(area) or not math.isfinite(current):
            raise ValueError(
                f"Design {index} in {csv_path} has non-finite area or current"
            )
        solutions.append({"area": area, "current": current})

    output_dir = PROJECT_DIR / "output_figs" / csv_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / "pareto.png"
    draw_pareto_front(solutions, plot_path, show_all=True)
    return plot_path.relative_to(PROJECT_DIR)


def main():
    parser = argparse.ArgumentParser(
        description="Find and display all designs with the maximum reward."
    )
    parser.add_argument("csv_file", type=Path, help="Path to a solutions CSV file")
    args = parser.parse_args()

    try:
        max_reward, best_designs, designs = find_best_designs(args.csv_file)
        plot_path = create_pareto_plot(args.csv_file, designs)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(2, f"Error: {error}\n")

    result = {
        "source": str(args.csv_file),
        "pareto_plot": str(plot_path),
        "max_reward": max_reward,
        "number_of_best_designs": len(best_designs),
        "best_designs": best_designs,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
