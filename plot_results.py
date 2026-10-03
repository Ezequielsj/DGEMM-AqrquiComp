import argparse
import csv
import html
import statistics
from collections import defaultdict


COLORS = {
    "baseline_python": "#555555",
    "c_baseline": "#0072B2",
    "c_avx": "#E69F00",
    "c_unrolled": "#009E73",
    "c_blocked": "#CC79A7",
    "c_openmp": "#D55E00",
}


def load_medians(csv_path):
    grouped = defaultdict(list)
    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            grouped[(row["version"], int(row["n"]))].append(float(row["gflops"]))

    medians = defaultdict(dict)
    for (version, size), values in grouped.items():
        medians[version][size] = statistics.median(values)
    return medians


def create_svg(medians, output_path):
    width, height = 1000, 570
    left, right, top, bottom = 100, 730, 65, 445
    sizes = sorted({size for results in medians.values() for size in results})
    if not sizes:
        raise ValueError("The CSV does not contain benchmark rows.")

    min_power, max_power = -2, 2

    def x_position(index):
        if len(sizes) == 1:
            return (left + right) / 2
        return left + index * (right - left) / (len(sizes) - 1)

    def y_position(value):
        if value <= 0:
            raise ValueError("GFLOPS values must be positive for logarithmic plotting.")
        import math

        power = math.log10(value)
        return bottom - (power - min_power) * (bottom - top) / (max_power - min_power)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<title>Median DGEMM throughput by matrix dimension</title>",
        "<desc>Median GFLOPS for each implementation, on a logarithmic vertical axis.</desc>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<g font-family="Arial, sans-serif" fill="#202124">',
        '<text x="100" y="32" font-size="20" font-weight="700">Median throughput by matrix dimension</text>',
    ]

    for power in range(min_power, max_power + 1):
        value = 10**power
        y = y_position(value)
        parts.extend(
            [
                f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#d9dee5" stroke-width="1"/>',
                f'<text x="{left - 14}" y="{y + 5:.1f}" text-anchor="end" font-size="13">{value:g}</text>',
            ]
        )

    parts.extend(
        [
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#39424e" stroke-width="1.5"/>',
            f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#39424e" stroke-width="1.5"/>',
            f'<text x="30" y="{(top + bottom) / 2:.0f}" text-anchor="middle" font-size="14" transform="rotate(-90 30 {(top + bottom) / 2:.0f})">GFLOPS (log scale)</text>',
            f'<text x="{(left + right) / 2:.0f}" y="{bottom + 53}" text-anchor="middle" font-size="14">Matrix dimension N x N</text>',
        ]
    )

    x_by_size = {}
    for index, size in enumerate(sizes):
        x = x_position(index)
        x_by_size[size] = x
        parts.extend(
            [
                f'<line x1="{x:.1f}" y1="{bottom}" x2="{x:.1f}" y2="{bottom + 5}" stroke="#39424e"/>',
                f'<text x="{x:.1f}" y="{bottom + 24}" text-anchor="middle" font-size="13">{size}</text>',
            ]
        )

    legend_y = top + 4
    for index, version in enumerate(COLORS):
        points = [
            (x_by_size[size], y_position(medians[version][size]))
            for size in sizes
            if size in medians.get(version, {})
        ]
        if points:
            color = COLORS[version]
            point_string = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
            parts.append(
                f'<polyline points="{point_string}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>'
            )
            for x, y in points:
                parts.append(
                    f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{color}" stroke="#ffffff" stroke-width="1.5"/>'
                )

        y = legend_y + index * 27
        parts.extend(
            [
                f'<line x1="770" y1="{y}" x2="798" y2="{y}" stroke="{COLORS[version]}" stroke-width="3"/>',
                f'<text x="808" y="{y + 5}" font-size="13">{html.escape(version)}</text>',
            ]
        )

    parts.extend(["</g>", "</svg>"])
    with open(output_path, "w", encoding="utf-8") as svg_file:
        svg_file.write("\n".join(parts) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Plot median GFLOPS from a benchmark CSV as an SVG chart."
    )
    parser.add_argument(
        "csv_path", nargs="?", default="benchmark_resultados_multidimensao.csv"
    )
    parser.add_argument("--output", default="grafico_desempenho.svg")
    args = parser.parse_args()
    create_svg(load_medians(args.csv_path), args.output)
    print(f"Chart written to: {args.output}")


if __name__ == "__main__":
    main()