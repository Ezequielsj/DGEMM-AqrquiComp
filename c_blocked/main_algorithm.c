#include <immintrin.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "../benchmark_helpers.h"

#define UNROLL (4)
#define BLOCKSIZE 32

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

void do_block (size_t n, size_t si, size_t sj, size_t sk,
               double *A, double *B, double *C)
{
    // The i-loop stride must be UNROLL * 4 = 16 for AVX2 (4 doubles per register)
    for (size_t i = si; i < si + BLOCKSIZE; i += UNROLL * 4)
    {
        for (size_t j = sj; j < sj + BLOCKSIZE; j++)
        {
            // Declare UNROLL (4) AVX2 registers for C[i..i+15][j]
            __m256d c[UNROLL];

            // Load the initial values of C[i..i+15][j]
            for (int r = 0; r < UNROLL; r++)
            {
                // Each load handles 4 doubles: offset r * 4
                c[r] = _mm256_load_pd(C + i + r * 4 + j * n);
            }

            for (size_t k = sk; k < sk + BLOCKSIZE; k++)
            {
                // Broadcast B[k][j] (B[k + j*n])
                __m256d bb = _mm256_broadcast_sd(B + k + j * n);

                for (int r = 0; r < UNROLL; r++)
                {
                    // Load A[i + r*4 .. i + r*4 + 3][k]
                    __m256d aa = _mm256_load_pd(A + k * n + r * 4 + i);

                    c[r] = _mm256_add_pd(c[r], _mm256_mul_pd(aa, bb));
                }
            }

            // Store the final accumulated values back into C
            for (int r = 0; r < UNROLL; r++)
            {
                _mm256_store_pd(C + i + r * 4 + j * n, c[r]);
            }
        }
    }
}

double dgemm (size_t n, double* A, double* B, double* C)
{
    double start = benchmark_now();
    for (size_t sj = 0; sj < n; sj += BLOCKSIZE)
        for (size_t si = 0; si < n; si += BLOCKSIZE)
            for (size_t sk = 0; sk < n; sk += BLOCKSIZE)
                do_block(n, si, sj, sk, A, B, C);
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
        fprintf(stderr, "Correctness validation failed for c_blocked.\n");
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
