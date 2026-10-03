#include <stdio.h>
#include <time.h>
#include <stdlib.h>
#include "../benchmark_helpers.h"


double dgemm (size_t n, double* A, double* B, double* C)
{    
    double start = benchmark_now();
    for (size_t i = 0; i < n; ++i)
        for (size_t j = 0; j < n; ++j)
        {
            double cij = C[i+j*n]; /* cij = C[i][j] */
            for (size_t k = 0; k < n; k++)
                cij += A[i+k*n] * B[k+j*n]; /* cij += A[i][k]*B[k][j] */
            C[i+j*n] = cij; /* C[i][j] = cij */
        }
    return benchmark_now() - start;
}



int main(int argc, char *argv[]) {
    double time_spent = 0.0;
    double end_time;
    int warmup_iterations;
    if (!benchmark_arguments(argc, argv, &end_time, &warmup_iterations)) {
        fprintf(stderr, "Usage: %s [duration_seconds] [warmup_iterations]\n", argv[0]);
        return 2;
    }
    size_t n;
    if (!benchmark_matrix_size(argc, argv, &n)) {
        fprintf(stderr, "Matrix size must be a multiple of 32 between 32 and 4096.\n");
        return 2;
    }
    int multiplication_count = 0;

    printf("Performing matrix multiplications of size %zux%zu for %f seconds.\n", n, n, end_time);

    srand(time(NULL));

    double *A = malloc((long long)n*n*sizeof(double));
    double *B = malloc((long long)n*n*sizeof(double));
    double *C = calloc((long long)n*n,sizeof(double));

    if (A == NULL || B == NULL || C == NULL) {
        fprintf(stderr, "Memory allocation failed for n = %zu\n", n);
        if (A) free(A);
        if (B) free(B);
        if (C) free(C);
        return 1;
    }

    for (size_t i = 0; i < n*n; i++) {
        A[i] = (double)rand() / RAND_MAX;
        B[i] = (double)rand() / RAND_MAX;
    }

    reset_output(C, n * n);
    dgemm(n, A, B, C);
    if (!validate_output(n, A, B, C)) {
        fprintf(stderr, "Correctness validation failed for c_baseline.\n");
        free(A); free(B); free(C);
        return 1;
    }
    for (int i = 1; i < warmup_iterations; ++i) {
        reset_output(C, n * n);
        dgemm(n, A, B, C);
    }

    while (time_spent < end_time) {
        reset_output(C, n * n);
        time_spent += dgemm(n, A, B, C);
        multiplication_count++;
    }

    printf("Result checksum: %.12g\n", output_checksum(C, n * n));

    free(A); free(B); free(C);

    printf("\n-------------------------------------------------\n");
    printf("Fixed N: %zu\n", n);
    printf("Number of multiplications performed: %d\n", multiplication_count);
    printf("Total computation time: %.6f seconds\n", time_spent);
    printf("-------------------------------------------------\n");

    return 0;
}