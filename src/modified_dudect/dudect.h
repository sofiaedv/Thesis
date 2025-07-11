/*
 dudect: dude, is my code constant time?
 https://github.com/oreparaz/dudect
 oscar.reparaz@esat.kuleuven.be

 Based on the following paper:

     Oscar Reparaz, Josep Balasch and Ingrid Verbauwhede
     dude, is my code constant time?
     DATE 2017
     https://eprint.iacr.org/2016/1123.pdf

 This file measures the execution time of a given function many times with
 different inputs and performs a Welch's t-test to determine if the function
 runs in constant time or not. This is essentially leakage detection, and
 not a timing attack.

 Notes:

   - the execution time distribution tends to be skewed towards large
     timings, leading to a fat right tail. Most executions take little time,
     some of them take a lot. We try to speed up the test process by
     throwing away those measurements with large cycle count. (For example,
     those measurements could correspond to the execution being interrupted
     by the OS.) Setting a threshold value for this is not obvious; we just
     keep the x% percent fastest timings, and repeat for several values of x.

   - the previous observation is highly heuristic. We also keep the uncropped
     measurement time and do a t-test on that.

   - we also test for unequal variances (second order test), but this is
     probably redundant since we're doing as well a t-test on cropped
     measurements (non-linear transform)

   - as long as any of the different test fails, the code will be deemed
     variable time.

 LICENSE:

    This is free and unencumbered software released into the public domain.
    Anyone is free to copy, modify, publish, use, compile, sell, or
    distribute this software, either in source code form or as a compiled
    binary, for any purpose, commercial or non-commercial, and by any
    means.
    In jurisdictions that recognize copyright laws, the author or authors
    of this software dedicate any and all copyright interest in the
    software to the public domain. We make this dedication for the benefit
    of the public at large and to the detriment of our heirs and
    successors. We intend this dedication to be an overt act of
    relinquishment in perpetuity of all present and future rights to this
    software under copyright law.
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
    OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
    For more information, please refer to <http://unlicense.org>
*/

/* Used for improved C++ compatibility */
#ifdef __cplusplus
extern "C" {
#endif

#ifndef DUDECT_IMPLEMENTATION

#ifndef DUDECT_H_INCLUDED
#define DUDECT_H_INCLUDED

#include <stddef.h>
#include <stdint.h>

#ifdef DUDECT_VISIBLITY_STATIC
#define DUDECT_VISIBILITY static
#else
#define DUDECT_VISIBILITY extern
#endif

/*
   The interface of dudect begins here, to be compiled only if DUDECT_IMPLEMENTATION is not defined.
   In a multi-file library what follows would be the public-facing dudect.h
*/

#define DUDECT_ENOUGH_MEASUREMENTS (10000) /* do not draw any conclusion before we reach this many measurements */
#define DUDECT_NUMBER_PERCENTILES  (100)

/* perform this many tests in total:
   - 1 first order uncropped test,
   - DUDECT_NUMBER_PERCENTILES tests
   - 1 second order test
*/
#define DUDECT_TESTS (1+DUDECT_NUMBER_PERCENTILES+1)

typedef struct {
  char identifier[100];
  int64_t measurement;
} csv_entry;

typedef struct {
  size_t chunk_size;
  size_t number_measurements;
} dudect_config_t;

typedef struct {
  double mean[2];
  double m2[2];
  double n[2];
} ttest_ctx_t;

typedef struct {
  int64_t *ticks;
  int64_t *exec_times;
  uint8_t *input_data;
  uint8_t *classes;
  dudect_config_t *config;
  ttest_ctx_t *ttest_ctxs[DUDECT_TESTS];
  int64_t *percentiles;
} dudect_ctx_t;

typedef enum {
  DUDECT_LEAKAGE_FOUND=11,
  DUDECT_NO_LEAKAGE_EVIDENCE_YET=10,
  DUDECT_DATA_EXHAUSTED=12
} dudect_state_t;

/* Public API */

DUDECT_VISIBILITY int dudect_init(dudect_ctx_t *ctx, dudect_config_t *conf);
DUDECT_VISIBILITY dudect_state_t dudect_main(dudect_ctx_t *c, const char* filename, int expectedLineCount);
DUDECT_VISIBILITY int dudect_free(dudect_ctx_t *ctx);
DUDECT_VISIBILITY void randombytes(uint8_t *x, size_t how_much);
DUDECT_VISIBILITY uint8_t randombit(void);

/* Public configuration */

/* Implementation details */
#include <inttypes.h>
#include <stdint.h>
#include <stddef.h>

#endif /* DUDECT_H_INCLUDED */

#else /* DUDECT_IMPLEMENTATION */

#undef DUDECT_IMPLEMENTATION
#include "dudect.h"
#define DUDECT_IMPLEMENTATION

/* The implementation of dudect begins here. In a multi-file library what follows would be dudect.c */

#define DUDECT_TRACE (0)

#include <assert.h>
#include <fcntl.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define MAX_BASELINE 500000
#define MAX_MODIFIED 500000
#define MAX_TOTAL (MAX_BASELINE + MAX_MODIFIED)

int runningCounter = 0;
int lastExitCode = 0;
int availableMeasurements = 0;
int baselineCount = 0;
int modifiedCount = 0;
csv_entry baselineCsvs[MAX_BASELINE];
csv_entry modifiedCsvs[MAX_MODIFIED];
csv_entry csvEntries[MAX_TOTAL];
bool readEntries = false;

/*
  Online Welch's t-test

  Tests whether two populations have same mean.
  This is basically Student's t-test for unequal
  variances and unequal sample sizes.

  see https://en.wikipedia.org/wiki/Welch%27s_t-test
 */
static void t_push(ttest_ctx_t *ctx, double x, uint8_t clazz) {
  assert(clazz == 0 || clazz == 1);
  ctx->n[clazz]++;
  /*
   estimate variance on the fly as per the Welford method.
   this gives good numerical stability, see Knuth's TAOCP vol 2
  */
  double delta = x - ctx->mean[clazz];
  ctx->mean[clazz] = ctx->mean[clazz] + delta / ctx->n[clazz];
  ctx->m2[clazz] = ctx->m2[clazz] + delta * (x - ctx->mean[clazz]);
}

static double t_compute(ttest_ctx_t *ctx) {
  double var[2] = {0.0, 0.0};
  var[0] = ctx->m2[0] / (ctx->n[0] - 1);
  var[1] = ctx->m2[1] / (ctx->n[1] - 1);
  double num = (ctx->mean[0] - ctx->mean[1]);
  double den = sqrt(var[0] / ctx->n[0] + var[1] / ctx->n[1]);
  double t_value = num / den;
  return t_value;
}

static void t_init(ttest_ctx_t *ctx) {
  for (int clazz = 0; clazz < 2; clazz ++) {
    ctx->mean[clazz] = 0.0;
    ctx->m2[clazz] = 0.0;
    ctx->n[clazz] = 0.0;
  }
}

static int cmp(const int64_t *a, const int64_t *b) {
    if (*a == *b)
        return 0;
    return (*a > *b) ? 1 : -1;
}

static int64_t percentile(int64_t *a_sorted, double which, size_t size) {
  size_t array_position = (size_t)((double)size * (double)which);
  assert(array_position < size);
  return a_sorted[array_position];
}

/*
 set different thresholds for cropping measurements.
 the exponential tendency is meant to approximately match
 the measurements distribution, but there's not more science
 than that.
*/
static void prepare_percentiles(dudect_ctx_t *ctx) {
  qsort(ctx->exec_times, ctx->config->number_measurements, sizeof(int64_t), (int (*)(const void *, const void *))cmp);
  for (size_t i = 0; i < DUDECT_NUMBER_PERCENTILES; i++) {
    ctx->percentiles[i] = percentile(
        ctx->exec_times, 1 - (pow(0.5, 10 * (double)(i + 1) / DUDECT_NUMBER_PERCENTILES)),
        ctx->config->number_measurements);
  }
}

/* this comes from ebacs */
void randombytes(uint8_t *x, size_t how_much) {
  ssize_t i;
  static int fd = -1;

  ssize_t xlen = (ssize_t)how_much;
  assert(xlen >= 0);
  if (fd == -1) {
    for (;;) {
      fd = open("/dev/urandom", O_RDONLY);
      if (fd != -1)
        break;
      sleep(1);
    }
  }

  while (xlen > 0) {
    if (xlen < 1048576)
      i = xlen;
    else
      i = 1048576;

    i = read(fd, x, (size_t)i);
    if (i < 1) {
      sleep(1);
      continue;
    }

    x += i;
    xlen -= i;
  }
}

uint8_t randombit(void) {
  uint8_t ret = 0;
  randombytes(&ret, 1);
  return (ret & 1);
}

/*
 Returns current CPU tick count from *T*ime *S*tamp *C*ounter.

 To enforce CPU to issue RDTSC instruction where we want it to, we put a `mfence` instruction before
 issuing `rdtsc`, which should make all memory load/ store operations, prior to RDTSC, globally visible.

 See https://github.com/oreparaz/dudect/issues/32
 See RDTSC documentation @ https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.htm#text=rdtsc&ig_expand=4395,5273
 See MFENCE documentation @ https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.htm#text=mfence&ig_expand=4395,5273,4395

 Also see https://stackoverflow.com/a/12634857
*/

// threshold values for Welch's t-test
#define t_threshold_bananas 500 // test failed, with overwhelming probability
#define t_threshold_moderate                                                   \
  10 // test failed. Pankaj likes 4.5 but let's be more lenient


static int readPreparedCsv(const char* fileName, int expectedLineCount) {

  if (fileName == NULL || expectedLineCount <= 0){
    return -1;
  }

  FILE *csvFile = fopen(fileName, "r");
  if (csvFile == NULL) {
    printf("Failed to open file.\n");
    return -1;
  }
  else {
    char lineBuffer[100];
    baselineCount = 0;
    modifiedCount = 0;

    for (int lineNumber = 0; lineNumber < expectedLineCount; ++lineNumber) {
      if (fgets(lineBuffer, sizeof(lineBuffer), csvFile) == NULL) {
        fclose(csvFile);
        return -1;
      }

      lineBuffer[strcspn(lineBuffer, "\r\n")] = 0;

      csv_entry newCsv;
      int scanResult;

      scanResult = sscanf(lineBuffer, "%99[^;];%lld", newCsv.identifier, &newCsv.measurement);
      if (scanResult == 2) {

        if (newCsv.identifier[0] == 'X') {
          if (baselineCount < MAX_BASELINE) {
            baselineCsvs[baselineCount++] = newCsv;
          } else {
            return -1;
          }
        } else {
          if (modifiedCount < MAX_MODIFIED) {
            modifiedCsvs[modifiedCount++] = newCsv;
          } else {
            return -1;
          }
        }
      } else {
        return -1;
      }
    }

    fclose(csvFile);

    int i = 0, j = 0, k = 0;
    int requiredTotalSize = baselineCount + modifiedCount;

    if (requiredTotalSize > MAX_TOTAL) {
      return -1;
    }

    while (i < baselineCount && j < modifiedCount) {
      csvEntries[k++] = baselineCsvs[i++];
      csvEntries[k++] = modifiedCsvs[j++];
    }

    while (i < baselineCount) {
      csvEntries[k++] = baselineCsvs[i++];
    }

    while (j < modifiedCount) {
      csvEntries[k++] = modifiedCsvs[j++];
    }

    return k;
  }
}

/*
static void measure(dudect_ctx_t *ctx, const char* fileName, int expectedLineCount) {
  if(!readEntries) {
    availableMeasurements = readPreparedCsv(fileName, expectedLineCount);
    printf("%d lines found\n", availableMeasurements);
    readEntries = true;
  }
  for (size_t i = 0; i < ctx->config->number_measurements; i++) {
    csv_entry listedEntry = csvEntries[runningCounter];
    ctx->exec_times[i] = listedEntry.measurement;
    ctx->classes[i] = listedEntry.identifier[0] == 'X' ? 0 : 1;
    runningCounter++;
    if(runningCounter >= availableMeasurements) {
    	printf("No more measurements available - quitting. \n");
		  exit(lastExitCode);
    }
  }
}
*/

static size_t measure(dudect_ctx_t *ctx, const char* fileName, int expectedLineCount) {
  size_t measurements_in_chunk = 0;

  if(!readEntries) {
    availableMeasurements = readPreparedCsv(fileName, expectedLineCount);
    printf("%d lines found\n", availableMeasurements);
    readEntries = true;
  }
  for (size_t i = 0; i < ctx->config->number_measurements; i++) {
    if(runningCounter >= availableMeasurements) {
		  break;
    }
    csv_entry listedEntry = csvEntries[runningCounter];
    ctx->exec_times[i] = listedEntry.measurement;
    ctx->classes[i] = listedEntry.identifier[0] == 'X' ? 0 : 1;
    runningCounter++;
    measurements_in_chunk++;
  }
  return measurements_in_chunk;
}

static void update_statistics(dudect_ctx_t *ctx, size_t no_chunk_measurements) {

  size_t start_index = 0;

  if (no_chunk_measurements <= start_index) {
    return;
  }

  for (size_t i = start_index; i < no_chunk_measurements; i++) {
    int64_t difference = ctx->exec_times[i];

    if (difference < 0) {
      continue; // the cpu cycle counter overflowed, just throw away the measurement
    }

    // t-test on the execution time
    t_push(ctx->ttest_ctxs[0], difference, ctx->classes[i]);

    // t-test on cropped execution times, for several cropping thresholds.
    for (size_t crop_index = 0; crop_index < DUDECT_NUMBER_PERCENTILES; crop_index++) {
      if (difference < ctx->percentiles[crop_index]) {
        t_push(ctx->ttest_ctxs[crop_index + 1], difference, ctx->classes[i]);
      }
    }

    // second-order test (only if we have more than 10000 measurements).
    // Centered product pre-processing.
    if (ctx->ttest_ctxs[0]->n[0] > 10000) {
      double centered = (double)difference - ctx->ttest_ctxs[0]->mean[ctx->classes[i]];
      t_push(ctx->ttest_ctxs[1 + DUDECT_NUMBER_PERCENTILES], centered * centered, ctx->classes[i]);
    }
  }
}

#if DUDECT_TRACE
static void report_test(ttest_ctx_t *x) {
  if (x->n[0] > DUDECT_ENOUGH_MEASUREMENTS) {
    double tval = t_compute(x);
    printf(" abs(t): %4.2f, number measurements: %f\n", tval, x->n[0]+x->n[1]);
  } else {
    printf(" (not enough measurements: %f + %f)\n", x->n[0], x->n[1]);
  }
}
#endif /* DUDECT_TRACE */

static ttest_ctx_t *max_test(dudect_ctx_t *ctx) {
  size_t ret = 0;
  double max = 0;
  for (size_t i = 0; i < DUDECT_TESTS; i++) {
    if (ctx->ttest_ctxs[i]->n[0] > DUDECT_ENOUGH_MEASUREMENTS) {
      double x = fabs(t_compute(ctx->ttest_ctxs[i]));
      if (max < x) {
        max = x;
        ret = i;
      }
    }
  }
  return ctx->ttest_ctxs[ret];
}

static dudect_state_t report(dudect_ctx_t *ctx) {

  #if DUDECT_TRACE
  for (size_t i = 0; i < DUDECT_TESTS; i++) {
    printf(" bucket %zu has %f measurements\n", i, ctx->ttest_ctxs[i]->n[0] +  ctx->ttest_ctxs[i]->n[1]);
  }

  printf("t-test on raw measurements\n");
  report_test(ctx->ttest_ctxs[0]);

  printf("t-test on cropped measurements\n");
  for (size_t i = 0; i < DUDECT_NUMBER_PERCENTILES; i++) {
    report_test(ctx->ttest_ctxs[i + 1]);
  }

  printf("t-test for second order leakage\n");
  report_test(ctx->ttest_ctxs[1 + DUDECT_NUMBER_PERCENTILES]);
  #endif /* DUDECT_TRACE */

  ttest_ctx_t *t = max_test(ctx);
  double max_t = fabs(t_compute(t));
  double number_traces_max_t = t->n[0] +  t->n[1];
  double max_tau = max_t / sqrt(number_traces_max_t);

  // print the number of measurements of the test that yielded max t.
  // sometimes you can see this number go down - this can be confusing
  // but can happen (different test)
  printf("meas: %7.2lf M, ", (number_traces_max_t / 1e6));
  if (number_traces_max_t < DUDECT_ENOUGH_MEASUREMENTS) {
    printf("not enough measurements (%.0f still to go).\n", DUDECT_ENOUGH_MEASUREMENTS-number_traces_max_t);
    return DUDECT_NO_LEAKAGE_EVIDENCE_YET;
  }

  /*
   * We report the following statistics:
   *
   * max_t: the t value
   * max_tau: a t value normalized by sqrt(number of measurements).
   *          this way we can compare max_tau taken with different
   *          number of measurements. This is sort of "distance
   *          between distributions", independent of number of
   *          measurements.
   * (5/tau)^2: how many measurements we would need to barely
   *            detect the leak, if present. "barely detect the
   *            leak" here means have a t value greater than 5.
   *
   * The first metric is standard; the other two aren't (but
   * pretty sensible imho)
   */
  printf("max t: %+7.2f, max tau: %.2e, (5/tau)^2: %.2e.",
    max_t,
    max_tau,
    (double)(5*5)/(double)(max_tau*max_tau));

  if (max_t > t_threshold_bananas) {
    lastExitCode = 11;
    printf(" Definitely not constant time.\n");
    return DUDECT_LEAKAGE_FOUND;
  }
  if (max_t > t_threshold_moderate) {
    lastExitCode = 11;
    printf(" Probably not constant time.\n");
    return DUDECT_LEAKAGE_FOUND;
  }
  if (max_t < t_threshold_moderate) {
    lastExitCode = 10;
    printf(" For the moment, maybe constant time.\n");
  }
  return DUDECT_NO_LEAKAGE_EVIDENCE_YET;
}

dudect_state_t dudect_main(dudect_ctx_t *ctx, const char* filename, int expectedLineCount) {
  bool first_time = ctx->percentiles[DUDECT_NUMBER_PERCENTILES - 1] == 0;

  size_t measurements_in_chunk = measure(ctx, filename, expectedLineCount);

  dudect_state_t ret = DUDECT_NO_LEAKAGE_EVIDENCE_YET;
  if (first_time) {
    // throw away the first batch of measurements.
    // this helps warming things up.
    if (measurements_in_chunk > 0) {
      prepare_percentiles(ctx);
    }
  } else {
    if (measurements_in_chunk > 0) {
      update_statistics(ctx, measurements_in_chunk);
    }
    ret = report(ctx);
  }

  if (runningCounter >= availableMeasurements) {
    if (ret == DUDECT_LEAKAGE_FOUND) {
      return DUDECT_LEAKAGE_FOUND;
    } else {
      return DUDECT_DATA_EXHAUSTED;
    }
  }

  return ret;
}

int dudect_init(dudect_ctx_t *ctx, dudect_config_t *conf)
{
  ctx->config = (dudect_config_t*) calloc(1, sizeof(*conf));
  ctx->config->number_measurements = conf->number_measurements;
  ctx->config->chunk_size = conf->chunk_size;
  ctx->ticks = (int64_t*) calloc(ctx->config->number_measurements, sizeof(int64_t));
  ctx->exec_times = (int64_t*) calloc(ctx->config->number_measurements, sizeof(int64_t));
  ctx->classes = (uint8_t*) calloc(ctx->config->number_measurements, sizeof(uint8_t));
  ctx->input_data = (uint8_t*) calloc(ctx->config->number_measurements * ctx->config->chunk_size, sizeof(uint8_t));

  for (int i = 0; i < DUDECT_TESTS; i++) {
    ctx->ttest_ctxs[i] = (ttest_ctx_t *)calloc(1, sizeof(ttest_ctx_t));
    assert(ctx->ttest_ctxs[i]);
    t_init(ctx->ttest_ctxs[i]);
  }

  ctx->percentiles = (int64_t*) calloc(DUDECT_NUMBER_PERCENTILES, sizeof(int64_t));

  assert(ctx->ticks);
  assert(ctx->exec_times);
  assert(ctx->classes);
  assert(ctx->input_data);
  assert(ctx->percentiles);

  return 0;
}

int dudect_free(dudect_ctx_t *ctx)
{
  for (int i = 0; i < DUDECT_TESTS; i++) {
    free(ctx->ttest_ctxs[i]);
  }
  free(ctx->percentiles);
  free(ctx->input_data);
  free(ctx->classes);
  free(ctx->exec_times);
  free(ctx->ticks);
  free(ctx->config);
  return 0;
}

#endif /* DUDECT_IMPLEMENTATION */

#ifdef __cplusplus
}  /* extern "C" */
#endif
