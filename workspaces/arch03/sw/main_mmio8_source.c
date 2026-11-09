#include "kwt.h"

/* The original PR #5 driver is linked without modification. Task data are
 * fetched through the original SysMem ICB source, never from the ITCM image. */
#ifndef KWT_MMIO8_TIMEOUT_CYCLES
#define KWT_MMIO8_TIMEOUT_CYCLES 100000000ull
#endif
#ifndef KWT_MMIO8_CLEAR_TIMEOUT_CYCLES
#define KWT_MMIO8_CLEAR_TIMEOUT_CYCLES 1000000ull
#endif

static inline void fence_io(void) {
    __asm__ volatile("fence iorw,iorw" ::: "memory");
}

static uint64_t cycles64(void) {
    uint32_t hi, lo, again;
    do {
        __asm__ volatile("csrr %0,mcycleh":"=r"(hi));
        __asm__ volatile("csrr %0,mcycle":"=r"(lo));
        __asm__ volatile("csrr %0,mcycleh":"=r"(again));
    } while(hi != again);
    return ((uint64_t)hi << 32) | lo;
}

int main(void) {
    volatile uint32_t *mail = (volatile uint32_t *)(uintptr_t)0xa001f000u;
    const volatile uint32_t *source = (const volatile uint32_t *)(uintptr_t)0xb0000000u;
    volatile uint32_t *shared32 = (volatile uint32_t *)(uintptr_t)KWT_SHARED_BASE;
    const volatile uint16_t *input = (const volatile uint16_t *)(uintptr_t)KWT_SHARED_BASE;
    volatile int16_t *output = (volatile int16_t *)(uintptr_t)0xa000c000u;
    const volatile uint32_t *metadata = (const volatile uint32_t *)(uintptr_t)0x8000fff0u;
    const volatile uint32_t *id_reg = (const volatile uint32_t *)(uintptr_t)(KWT_BASE + KWT_ID);
    const volatile uint32_t *status_reg = (const volatile uint32_t *)(uintptr_t)(KWT_BASE + KWT_STATUS);
    struct kwt_stats stats = {0, 0, 0, 0};
    uint64_t before = 0, elapsed = 0, copy_cycles = 0, clear_start;
    uint32_t shift = metadata[0], copied = 0, cleared_status = 0xffffffffu;
    int rc = KWT_OK;
    mail[0] = 0;
    mail[8] = 0;
    /* CONTROL=2 resets all accelerator valid state. Wait for the observed
     * reset/idle state before the first source read, including on warm reuse. */
    kwt_abort();
    clear_start = cycles64();
    if(*id_reg != 0x4b575403u || shift > 31u) {
        rc = KWT_DEVICE_ERROR;
        goto complete;
    }
    do {
        cleared_status = *status_reg;
        if((cleared_status & 31u) == 0) break;
        if(cycles64() - clear_start >= KWT_MMIO8_CLEAR_TIMEOUT_CYCLES) {
            rc = KWT_TIMEOUT;
            goto complete;
        }
    } while(1);
    fence_io();
    before = cycles64();
    /* This legacy marker only arms the observer. Official elapsed cycles start
     * when the first source request VALID is issued, including its ready wait. */
    mail[8] = 0x4b575442u;
    fence_io();
    {
        uint64_t copy_start = cycles64();
        for(copied = 0; copied < KWT_LOAD_WORDS / 2u; ++copied)
            shared32[copied] = source[copied];
        fence_io();
        copy_cycles = cycles64() - copy_start;
    }
    if(cycles64() - before >= KWT_MMIO8_TIMEOUT_CYCLES) {
        rc = KWT_TIMEOUT;
    } else {
        /* Preserve the original abort, polling, divisions, halfword reads and
         * output SH stores. This is the original driver, not the PR #6 rewrite. */
        rc = kwt_run_layer(input, output, shift, KWT_MMIO8_TIMEOUT_CYCLES, &stats);
    }
    fence_io();
    elapsed = cycles64() - before;
complete:
    if(rc != KWT_OK) kwt_abort();
    mail[1] = (uint32_t)rc;
    mail[2] = stats.input_words;
    mail[3] = stats.output_words;
    mail[4] = (uint32_t)elapsed;
    mail[5] = (uint32_t)(elapsed >> 32);
    mail[6] = stats.saturated;
    mail[7] = 0x4b575403u;
    mail[9] = copied;                 /* software copies, not measured bus ACKs */
    mail[10] = 0x00080001u;            /* manifest layout tag, not a new MMIO ABI */
    mail[11] = 0xb0000000u;
    mail[12] = 2u * KWT_LOAD_WORDS;
    mail[13] = 2u * KWT_OUTPUT_WORDS;
    mail[14] = (uint32_t)copy_cycles;
    mail[15] = (uint32_t)(copy_cycles >> 32);
    mail[16] = (uint32_t)stats.cycles;
    mail[17] = (uint32_t)(stats.cycles >> 32);
    mail[18] = cleared_status;
    mail[19] = shift;
    mail[20] = 0x4d385331u;            /* M8S1: program-only SysMem source build */
    fence_io();
    mail[0] = rc ? 0xbad00002u : 0x4b575450u;
    for(;;) __asm__ volatile("nop");
}
