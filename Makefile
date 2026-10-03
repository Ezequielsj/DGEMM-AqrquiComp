# Makefile for Compiling Matrix Multiplication Examples

CC ?= gcc
CFLAGS ?= -O3 -Wall -Wno-unknown-pragmas
LDLIBS ?= -lm

AVX_FLAGS = -mavx2 -mfma
OMP_FLAGS = -fopenmp

# Detect MKL on Linux/WSL and Windows if present.
MKL_INCLUDE =
MKL_LIB_PATH =
INTEL_COMPILER_LIB_PATH =
MKL_LIBS =

ifneq ($(wildcard /opt/intel/oneapi/mkl/latest/include/mkl.h),)
	MKL_INCLUDE = -I/opt/intel/oneapi/mkl/latest/include
	MKL_LIB_PATH = -L/opt/intel/oneapi/mkl/latest/lib/intel64
	INTEL_COMPILER_LIB_PATH = -L/opt/intel/oneapi/compiler/latest/linux/compiler/lib/intel64_lin
	MKL_LIBS = -lmkl_rt -liomp5 -lpthread -lm -ldl
endif

ifneq ($(wildcard /usr/include/mkl.h),)
	MKL_INCLUDE = -I/usr/include
	MKL_LIB_PATH =
	MKL_LIBS = -lmkl_rt
endif

# Define all targets
all: c_baseline c_avx c_unrolled c_blocked c_openmp mkl_lib

# --- Alias names to match the Python orchestrator ---
baseline_python:
	@echo "Python benchmark; no compilation needed."
c_baseline: c_baseline_bin
c_avx: c_avx_bin
c_unrolled: c_unrolled_bin
c_blocked: c_blocked_bin
c_openmp: c_openmp_bin
mkl_lib: mkl_lib_bin

# --- Benchmark-specific rules ---
c_baseline_bin: c_baseline/program
c_baseline/program: c_baseline/main_algorithm.c benchmark_helpers.h
	$(CC) $(CFLAGS) -o "$@" "$<" $(LDLIBS)

c_avx_bin: c_avx/program
c_avx/program: c_avx/main_algorithm.c benchmark_helpers.h
	$(CC) $(CFLAGS) $(AVX_FLAGS) -o "$@" "$<" $(LDLIBS)

c_unrolled_bin: c_unrolled/program
c_unrolled/program: c_unrolled/main_algorithm.c benchmark_helpers.h
	$(CC) $(CFLAGS) $(AVX_FLAGS) -o "$@" "$<" $(LDLIBS)

c_blocked_bin: c_blocked/program
c_blocked/program: c_blocked/main_algorithm.c benchmark_helpers.h
	$(CC) $(CFLAGS) $(AVX_FLAGS) -o "$@" "$<" $(LDLIBS)

c_openmp_bin: c_openmp/program
c_openmp/program: c_openmp/main_algorithm.c benchmark_helpers.h
	$(CC) $(CFLAGS) $(AVX_FLAGS) $(OMP_FLAGS) -o "$@" "$<" $(LDLIBS)

# MKL is optional. The benchmark should still run on systems without the Intel library.
mkl_lib_bin: mkl_lib/program
mkl_lib/program: mkl_lib/main_algorithm.c
	@if [ -z "$(MKL_INCLUDE)" ] || [ -z "$(MKL_LIBS)" ]; then \
		echo "MKL is not available in this environment; skipping MKL benchmark."; \
		exit 0; \
	fi; \
	$(CC) $(CFLAGS) $(MKL_INCLUDE) -o "$@" "$<" $(MKL_LIB_PATH) $(INTEL_COMPILER_LIB_PATH) $(MKL_LIBS)

# --- Housekeeping rules ---
clean:
	rm -f c_baseline/program c_avx/program c_unrolled/program c_blocked/program c_openmp/program mkl_lib/program

.PHONY: all clean baseline_python c_baseline c_avx c_unrolled c_blocked c_openmp mkl_lib
