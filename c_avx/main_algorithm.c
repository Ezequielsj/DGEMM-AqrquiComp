#include <immintrin.h>
#include <stddef.h>
#include <stdio.h>
#include <time.h>
#include <stdlib.h>
#include "../benchmark_helpers.h"

static void *aligned_alloc64(size_t size)
{
    void *ptr = NULL;
    if (posix_memalign(&ptr, 32, size) != 0) {
        return NULL;
    }
    return ptr;
}

static void aligned_free64(void *ptr)
{
    free(ptr);
}

double dgemm (size_t n, double* A, double* B, double* C)
{
    double start = benchmark_now();
    for ( size_t i = 0; i < n; i+=4 )
        for ( size_t j = 0; j < n; j++ ) {
            __m256d c0 = _mm256_load_pd(C+i+j*n); /* c0 = C[i][j] */
            for( size_t k = 0; k < n; k++ )
                c0 = _mm256_add_pd(c0, /* c0 += A[i][k]*B[k][j] */
                _mm256_mul_pd(_mm256_load_pd(A+i+k*n),
                _mm256_broadcast_sd(B+k+j*n)));
            _mm256_store_pd(C+i+j*n, c0); /* C[i][j] = c0 */
        }
    return benchmark_now() - start;
}

int main(int argc, char *argv[]) {
    double time_spent = 0.0;
    double end_time;
    int warmup_iterations;
    if (!benchmark_arguments(argc, argv, &end_time, &warmup_iterations)) {
        fprintf(stderr, "Usage: %s [duration_seconds] [warmup_iterations] [matrix_size]\n", argv[0]);
        return 2;
    }
    size_t n;
    if (!benchmark_matrix_size(argc, argv, &n)) {
        fprintf(stderr, "Matrix size must be a multiple of 32 between 32 and 4096.\n");
        return 2;
    }
    int multiplication_count = 0;
    
    printf("Performing matrix multiplications of size %llux%llu for %f seconds.\n", (unsigned long long)n, (unsigned long long)n, end_time);

    srand(time(NULL));

    // Align memory for AVX
    double *A = aligned_alloc64(n*n*sizeof(double));
    double *B = aligned_alloc64(n*n*sizeof(double));
    double *C = aligned_alloc64(n*n*sizeof(double));

    if (A == NULL || B == NULL || C == NULL) {
        fprintf(stderr, "Memory allocation failed for n = %llu\n", (unsigned long long)n);
        if (A) aligned_free64(A);
        if (B) aligned_free64(B);
        if (C) aligned_free64(C);
        return 1;
    }

    // Initialize C to zeros and A, B with random values
    for (size_t i = 0; i < n*n; i++) {
        C[i] = 0.0;
        A[i] = (double)rand() / RAND_MAX;
        B[i] = (double)rand() / RAND_MAX;
    }

    reset_output(C, n * n);
    dgemm(n, A, B, C);
    if (!validate_output(n, A, B, C)) {
        fprintf(stderr, "Correctness validation failed for c_avx.\n");
        aligned_free64(A); aligned_free64(B); aligned_free64(C);
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

    aligned_free64(A); 
    aligned_free64(B); 
    aligned_free64(C);

    printf("\n-------------------------------------------------\n");
    printf("Fixed N: %llu\n", (unsigned long long)n);
    printf("Number of multiplications performed: %d\n", multiplication_count);
    printf("Total computation time: %.6f seconds\n", time_spent);
    printf("-------------------------------------------------\n");

    return 0;
}
