#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include "../../../../../pq-crystals-kyber-12/kyber/ref/api.h"  // Adjust this path based on your setup
//#include "../../../../../pq-crystals-kyber-12/kyber/ref/randombytes.h"

#define DECAPSULATION_KEY_LENGTH 1632
#define CIPHERTEXT_LENGTH 768
#define SHARED_SECRET_LENGTH 32

static uint64_t rdtsc() {
	unsigned int lo, hi;
	__asm__ __volatile__ ("sfence");
	__asm__ __volatile__ ("lfence");
	__asm__ __volatile__ ("mfence");
	__asm__ __volatile__ ("rdtsc" : "=a" (lo), "=d" (hi));
	return ((uint64_t) hi << 32) | lo;
}

int main() {
    unsigned char decapsulation_key[DECAPSULATION_KEY_LENGTH];  // Secret Key
    unsigned char ciphertext[CIPHERTEXT_LENGTH];  // Ciphertext
    unsigned char shared_secret[SHARED_SECRET_LENGTH];  // Shared Secret (Encapsulation)

    size_t bytes_read;
    uint64_t before, after;

    bytes_read = fread(decapsulation_key, 1, DECAPSULATION_KEY_LENGTH, stdin);
    bytes_read = fread(ciphertext, 1, CIPHERTEXT_LENGTH, stdin);

    before = rdtsc();
    pqcrystals_kyber512_ref_dec(shared_secret, ciphertext, decapsulation_key);
    after = rdtsc();

    printf("%lu", after - before);

    return 0;
}
