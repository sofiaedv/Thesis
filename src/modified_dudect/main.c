#include <stdio.h>
#include <stdlib.h>
#include <unistd.h> // getopt (Linux/macOS standard)
#include <string.h>

#define DUDECT_IMPLEMENTATION
#include "dudect.h"

#define DUDECT_CHUNK_SIZE 10000

void print_usage(const char *prog_name) {
    fprintf(stderr, "Usage: %s -f <csv_filepath> -n <expected_line_count>\n", prog_name);
    fprintf(stderr, "  -f <csv_filepath>: Path to the CSV file (Mona format: ID;measurement\\n)\n");
    fprintf(stderr, "  -n <expected_line_count>: Total number of data lines in the CSV file.\n");
}

int main(int argc, char *argv[]) {
    char *csv_filename = NULL;
    int expected_lines = -1;
    int opt;

    while ((opt = getopt(argc, argv, "f:n:")) != -1) {
        switch (opt) {
            case 'f':
                csv_filename = optarg;
                break;
            case 'n':
                expected_lines = atoi(optarg); // Convert string to integer
                break;
            case '?': // Handle unknown options or missing option arguments
                fprintf(stderr, "Error: Unknown option or missing argument.\n");
                print_usage(argv[0]);
                return EXIT_FAILURE;
            default:
                print_usage(argv[0]);
                return EXIT_FAILURE;
        }
    }

    if (csv_filename == NULL) {
        fprintf(stderr, "Error: CSV filepath (-f) is required.\n");
        print_usage(argv[0]);
        return EXIT_FAILURE;
    }
    if (expected_lines <= 0) {
        fprintf(stderr, "Error: Invalid or missing expected line count (-n).\n");
        print_usage(argv[0]);
        return EXIT_FAILURE;
    }
    if (optind < argc) {
        fprintf(stderr, "Error: Unexpected positional arguments found after options.\n");
        print_usage(argv[0]);
        return EXIT_FAILURE;
    }

    dudect_config_t conf = {0};
    conf.number_measurements = DUDECT_CHUNK_SIZE;
    conf.chunk_size = 1;

    dudect_ctx_t ctx = {0};
    if (dudect_init(&ctx, &conf) != 0) {
        fprintf(stderr, "Error: Failed to initialize dudect context.\n");
        return EXIT_FAILURE;
    }

    dudect_state_t state = DUDECT_NO_LEAKAGE_EVIDENCE_YET;

    while (state == DUDECT_NO_LEAKAGE_EVIDENCE_YET) {
        state = dudect_main(&ctx, csv_filename, expected_lines);
    }

    dudect_free(&ctx);

    if (state == DUDECT_LEAKAGE_FOUND) {
        return 11; // Return the leakage code
    } else if (state == DUDECT_DATA_EXHAUSTED) {
        return 10;
    } else {
        return 10; // Return the no-leakage code
    }
    // Should not be reached
    return EXIT_SUCCESS;
}
