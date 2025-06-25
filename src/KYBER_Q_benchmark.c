#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include <time.h>
#define KYBER_Q 3329

static uint64_t rdtsc() {
	unsigned int lo, hi;
	__asm__ __volatile__ ("sfence");
	__asm__ __volatile__ ("lfence");
	__asm__ __volatile__ ("mfence");
	__asm__ __volatile__ ("rdtsc" : "=a" (lo), "=d" (hi));
	return ((uint64_t) hi << 32) | lo;
}

typedef struct {
    uint64_t value;
    int index;
} ValIndex;

int compare_by_value(const void *a, const void *b) {
    const ValIndex *va = (const ValIndex *)a;
    const ValIndex *vb = (const ValIndex *)b;
    if (va->value < vb->value) return -1;
    if (va->value > vb->value) return 1;
    return 0;
}

int main(int argc, char *argv[]) {
    int rows = KYBER_Q, columns = 1000000;
    uint64_t result_sum[KYBER_Q] = {0};

    volatile uint32_t numerator;
    volatile uint32_t division_result;
    volatile uint32_t random_thing;

    uint64_t before, after;

    if (argc != 2) {
        fprintf(stderr, "Usage: %s <divisor>\n", argv[0]);
        return 1;
    }

    volatile uint32_t divisor = atoi(argv[1]);

    for (int j = 0; j < columns; j++) {
        for (int i = 0; i < rows; i++) {
            numerator = i;
            volatile uint32_t actual_numerator = (numerator << 1) + (divisor/2);
            before = rdtsc();
            division_result  = numerator / divisor;
            after = rdtsc();

            random_thing += division_result;

            result_sum[i] += (after - before);
        }
    }

    ValIndex valArrSum[KYBER_Q];
    for (int i = 0; i < KYBER_Q; i++) {
        valArrSum[i].value = result_sum[i];
        valArrSum[i].index = i;
    }

    qsort(valArrSum, KYBER_Q, sizeof(ValIndex), compare_by_value);

    for (int i = 0; i < KYBER_Q; i++) {
        printf("%d (value = %" PRIu64 ")\n", valArrSum[i].index, valArrSum[i].value);
    }

    return 0;
}
