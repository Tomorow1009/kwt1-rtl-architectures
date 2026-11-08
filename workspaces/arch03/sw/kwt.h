#ifndef KWT_ARCH03_H
#define KWT_ARCH03_H
#include <stdint.h>
#define KWT_BASE 0x40000000u
#define KWT_SHARED_BASE 0xa0000000u
#define KWT_SHARED_BYTES 0x80000u
#define KWT_LOAD_WORDS 23488u
#define KWT_OUTPUT_WORDS 25344u
enum kwt_reg { KWT_ID=0, KWT_CONTROL=4, KWT_STATUS=8, KWT_SHIFT=12,
    KWT_LOAD=16, KWT_OUTPUT=20, KWT_LOAD_COUNT=24, KWT_OUTPUT_COUNT=28, KWT_ERROR=32 };
enum kwt_result { KWT_OK=0,KWT_TIMEOUT=-1,KWT_DEVICE_ERROR=-2,KWT_BAD_OUTPUT=-3,KWT_BAD_ARGUMENT=-4 };
struct kwt_stats { uint64_t cycles; uint32_t input_words,output_words,saturated; };
// load is the existing arch02 packed stream; output is signed row-major 99x256.
// Both arrays must reside in the mapped shared SRAM, without overlap.
int kwt_run_layer(const volatile uint16_t *load,volatile int16_t *output,
    unsigned shift,uint64_t timeout_cycles,struct kwt_stats *stats);
void kwt_abort(void);
#endif
