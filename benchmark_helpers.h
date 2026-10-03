#ifndef BENCHMARK_HELPERS_H
#define BENCHMARK_HELPERS_H

#include <math.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double benchmark_now(void)
{
    struct timespec timestamp;
    clock_gettime(CLOCK_MONOTONIC, &timestamp);
    return (double)timestamp.tv_sec + (double)timestamp.tv_nsec / 1e9;
}

static void reset_output(double *C, size_t element_count)
{
    memset(C, 0, element_count * sizeof(*C));
}

static double output_checksum(const double *C, size_t element_count)
{
    double checksum = 0.0;
    for (size_t i = 0; i < element_count; ++i) {
        checksum += C[i];
    }
    return checksum;
}

static int validate_output(size_t n, const double *A, const double *B,
                           const double *C)
{
    for (size_t j = 0; j < n; ++j) {
        for (size_t i = 0; i < n; ++i) {
            double expected = 0.0;
            for (size_t k = 0; k < n; ++k) {
                expected += A[i + k * n] * B[k + j * n];
            }
            double actual = C[i + j * n];
            double tolerance = 1e-9 * fmax(1.0, fabs(expected));
            if (!isfinite(actual) || fabs(actual - expected) > tolerance) {
                return 0;
            }
        }
    }
    return 1;
}

static int benchmark_arguments(int argc, char **argv, double *duration,
                               int *warmup_iterations)
{
    *duration = argc > 1 ? atof(argv[1]) : 10.0;
    *warmup_iterations = argc > 2 ? atoi(argv[2]) : 1;
    return isfinite(*duration) && *duration > 0.0 && *warmup_iterations >= 0;
}

static int benchmark_matrix_size(int argc, char **argv, size_t *n)
{
    char *end = NULL;
    unsigned long long parsed = argc > 3 ? strtoull(argv[3], &end, 10) : 512;
    if ((argc > 3 && (end == argv[3] || *end != '\0')) ||
        parsed < 32 || parsed > 4096 || parsed % 32 != 0) {
        return 0;
    }
    *n = (size_t)parsed;
    return 1;
}

#endif