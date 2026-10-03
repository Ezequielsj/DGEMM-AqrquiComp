import argparse
import csv
import os
import platform
import re
import statistics
import subprocess
import sys
from datetime import datetime


def default_interpreter():
    if sys.executable and os.path.exists(sys.executable):
        return sys.executable
    for candidate in ("python3", "python"):
        try:
            result = subprocess.run(
                [candidate, "--version"], capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                return candidate
        except FileNotFoundError:
            pass
    return "python3"


def system_metadata(thread_count):
    cpu_model = platform.processor() or "unknown"
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as cpuinfo:
            for line in cpuinfo:
                if line.lower().startswith("model name"):
                    cpu_model = line.split(":", 1)[1].strip()
                    break
    except OSError:
        pass

    memory_gib = "unknown"
    try:
        with open("/proc/meminfo", encoding="utf-8") as meminfo:
            for line in meminfo:
                if line.startswith("MemTotal:"):
                    memory_kib = int(line.split()[1])
                    memory_gib = f"{memory_kib / 1048576:.2f}"
                    break
    except (OSError, ValueError):
        pass

    return {
        "cpu_model": cpu_model,
        "logical_cpus": os.cpu_count() or "unknown",
        "memory_gib": memory_gib,
        "omp_threads": thread_count,
        "platform": platform.platform(),
    }


CONFIG = {
    "baseline_python": {
        "path": "baseline_python/main_algorithm.py",
        "type": "python",
        "interpreter": os.environ.get("PYTHON", default_interpreter()),
    },
    "c_baseline": {"path": "c_baseline/program", "type": "c"},
    "c_avx": {"path": "c_avx/program", "type": "c"},
    "c_unrolled": {"path": "c_unrolled/program", "type": "c"},
    "c_blocked": {"path": "c_blocked/program", "type": "c"},
    "c_openmp": {"path": "c_openmp/program", "type": "c"},
    "mkl_lib": {"path": "mkl_lib/program", "type": "c"},
    "torch_cpu": {
        "path": "torch_cpu/main_algorithm.py",
        "type": "python",
        "interpreter": os.environ.get("PYTHON", default_interpreter()),
    },
    "torch_gpu": {
        "path": "torch_gpu/main_algorithm.py",
        "type": "python",
        "interpreter": os.environ.get("PYTHON", default_interpreter()),
    },
}

DEFAULT_VERSIONS = [
    "baseline_python",
    "c_baseline",
    "c_avx",
    "c_unrolled",
    "c_blocked",
    "c_openmp",
]


def compile_code(version, project_dir):
    config = CONFIG[version]
    if config["type"] != "c":
        return True

    result = subprocess.run(
        ["make", version], capture_output=True, text=True, check=False, cwd=project_dir
    )
    if result.returncode != 0:
        print(f"--- ERROR: Compilation of {version} failed. ---")
        print(result.stderr.strip() or result.stdout.strip())
        return False

    executable_path = os.path.join(project_dir, config["path"])
    if not os.path.isfile(executable_path):
        print(f"--- ERROR: Executable for {version} was not produced. ---")
        print(result.stdout.strip() or "The optional library may not be installed.")
        return False

    if result.stdout.strip():
        print(result.stdout.strip())
    return True


def run_and_parse(version, duration, warmup_iterations, matrix_size, thread_count, project_dir):
    config = CONFIG[version]
    executable_path = os.path.join(project_dir, config["path"])
    args = [str(duration), str(warmup_iterations), str(matrix_size)]

    if config["type"] == "python":
        command = [config["interpreter"], executable_path, *args]
    else:
        command = [executable_path, *args]

    environment = os.environ.copy()
    environment["OMP_NUM_THREADS"] = str(thread_count)
    environment["OMP_DYNAMIC"] = "FALSE"

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            cwd=project_dir,
            env=environment,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        print(f"--- ERROR: Failed to run {version}: {error} ---")
        if getattr(error, "stderr", None):
            print(error.stderr.strip())
        return None

    print(result.stdout)
    n_match = re.search(r"Fixed N: (\d+)", result.stdout)
    mult_match = re.search(r"Number of multiplications performed: (\d+)", result.stdout)
    time_match = re.search(r"Total computation time: ([\d.]+) seconds", result.stdout)
    checksum_match = re.search(r"Result checksum: ([\d.eE+-]+)", result.stdout)

    if not (n_match and mult_match and time_match):
        print(f"--- ERROR: Could not parse output for {version}. ---")
        return None
    if config["type"] == "c" and not checksum_match:
        print(f"--- ERROR: Correctness checksum missing for {version}. ---")
        return None

    n = int(n_match.group(1))
    multiplications = int(mult_match.group(1))
    total_time = float(time_match.group(1))
    if n != matrix_size or multiplications <= 0 or total_time <= 0:
        print(f"--- ERROR: Invalid measurement values for {version}. ---")
        return None

    gflops = 2 * (n**3) * multiplications / (total_time * 1e9)
    return {
        "n": n,
        "multiplications": multiplications,
        "total_time": total_time,
        "gflops": gflops,
        "checksum": checksum_match.group(1) if checksum_match else "",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }


def positive_float(value):
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def nonnegative_int(value):
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return number


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def matrix_size_argument(value):
    number = positive_int(value)
    if number < 32 or number > 4096 or number % 32 != 0:
        raise argparse.ArgumentTypeError(
            "matrix size must be a multiple of 32 between 32 and 4096"
        )
    return number


def main():
    parser = argparse.ArgumentParser(
        description="Run repeated matrix multiplication benchmarks and collect results."
    )
    parser.add_argument(
        "--versions", nargs="+", default=DEFAULT_VERSIONS,
        choices=CONFIG.keys(), help="Benchmark variants to run."
    )
    parser.add_argument(
        "--sizes", nargs="+", type=matrix_size_argument, default=[512],
        help="Matrix dimensions; must be multiples of 32 from 32 to 4096."
    )
    parser.add_argument(
        "--num_iterations", "--num-iterations", type=nonnegative_int, default=5,
        help="Independent measured runs per variant (default: 5)."
    )
    parser.add_argument(
        "--seconds", type=positive_float, default=10.0,
        help="Target measured duration for each run, in seconds (default: 10)."
    )
    parser.add_argument(
        "--warmup_iterations", "--warmup-iterations", type=nonnegative_int, default=1,
        help="Unmeasured warm-up multiplications per run (default: 1)."
    )
    parser.add_argument(
        "--threads", type=positive_int, default=4,
        help="Fixed OpenMP thread count (default: 4)."
    )
    parser.add_argument("--output_csv", "--output-csv", help="Output CSV path.")
    args = parser.parse_args()
    if args.num_iterations == 0:
        parser.error("--num_iterations must be greater than zero")
    if len(set(args.sizes)) != len(args.sizes):
        parser.error("--sizes cannot contain duplicates")
    optional_versions = set(args.versions) - set(DEFAULT_VERSIONS)
    if optional_versions and args.sizes != [512]:
        parser.error("The optional MKL/PyTorch variants are currently fixed at size 512")

    project_dir = os.path.dirname(os.path.abspath(__file__))
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = args.output_csv or f"benchmark_resultados_{run_id}.csv"
    output_path = os.path.abspath(output_csv)
    metadata = system_metadata(args.threads)
    fieldnames = [
        "run_id", "version", "iteration", "n", "multiplications",
        "total_time", "gflops", "checksum", "timestamp", "cpu_model",
        "logical_cpus", "memory_gib", "omp_threads", "platform",
    ]
    failures = 0

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        compiled = {
            version: compile_code(version, project_dir) for version in args.versions
        }
        for version, success in compiled.items():
            if not success:
                failures += args.num_iterations * len(args.sizes)

        for matrix_size in args.sizes:
            print(f"=== Matrix dimension: {matrix_size}x{matrix_size} ===")
            for version in args.versions:
                if not compiled[version]:
                    continue

                measurements = []
                print(
                    f"--- {version}: {args.num_iterations} repetitions, "
                    f"{args.seconds:g}s each, {args.warmup_iterations} warm-ups, "
                    f"{args.threads} OpenMP threads. ---"
                )
                for iteration in range(1, args.num_iterations + 1):
                    print(f"--- Running iteration {iteration}/{args.num_iterations} ---")
                    measurement = run_and_parse(
                        version,
                        args.seconds,
                        args.warmup_iterations,
                        matrix_size,
                        args.threads,
                        project_dir,
                    )
                    if measurement is None:
                        failures += 1
                        continue

                    writer.writerow(
                        {
                            "run_id": run_id,
                            "version": version,
                            "iteration": iteration,
                            **measurement,
                            **metadata,
                        }
                    )
                    csvfile.flush()
                    measurements.append(measurement)

                if measurements:
                    median_gflops = statistics.median(
                        item["gflops"] for item in measurements
                    )
                    print(
                        f"--- {version} n={matrix_size}: "
                        f"{len(measurements)}/{args.num_iterations} válidas; "
                        f"mediana {median_gflops:.4f} GFLOPS. ---"
                    )

    print(f"Results written to: {output_path}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())