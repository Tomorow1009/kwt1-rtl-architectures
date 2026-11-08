#include "kwt.h"
int main(void) {
    volatile uint32_t *mail=(volatile uint32_t *)(uintptr_t)0xa001f000u;
    const volatile uint16_t *source=(const volatile uint16_t *)(uintptr_t)0x80010000u;
    volatile uint16_t *input=(volatile uint16_t *)(uintptr_t)KWT_SHARED_BASE;
    volatile int16_t *output=(volatile int16_t *)(uintptr_t)0xa000c000u;
    const volatile uint32_t *metadata=(const volatile uint32_t *)(uintptr_t)0x8000fff0u;
    struct kwt_stats stats;
    uint32_t before_lo,before_hi,after_lo,after_hi,again;
    int rc;
    mail[0]=0;
    // Invalidate prior task state before the measured load window. Physical SRAM
    // contents remain; every new task must supply all input and parameter words.
    kwt_abort();
    do { __asm__ volatile("csrr %0,mcycleh":"=r"(before_hi));
         __asm__ volatile("csrr %0,mcycle":"=r"(before_lo));
         __asm__ volatile("csrr %0,mcycleh":"=r"(again)); } while(before_hi!=again);
    // The passive bus observer starts at this store's successful response.
    // The fence ensures no source input read precedes that boundary.
    mail[8]=0x4b575442u;
    __asm__ volatile("fence iorw,iorw" ::: "memory");
    // Initial layer loading occurs through E203's actual system bus, not a TB force.
    for(unsigned i=0;i<KWT_LOAD_WORDS;i++) input[i]=source[i];
    __asm__ volatile("fence iorw,iorw" ::: "memory");
    rc=kwt_run_layer(input,output,metadata[0],100000000u,&stats);
    do { __asm__ volatile("csrr %0,mcycleh":"=r"(after_hi));
         __asm__ volatile("csrr %0,mcycle":"=r"(after_lo));
         __asm__ volatile("csrr %0,mcycleh":"=r"(again)); } while(after_hi!=again);
    uint64_t elapsed=(((uint64_t)after_hi<<32)|after_lo)-(((uint64_t)before_hi<<32)|before_lo);
    mail[1]=(uint32_t)rc;mail[2]=stats.input_words;mail[3]=stats.output_words;
    mail[4]=(uint32_t)elapsed;mail[5]=(uint32_t)(elapsed>>32);mail[6]=stats.saturated;
    __asm__ volatile("fence iorw,iorw" ::: "memory");
    mail[0]=rc ? 0xbad00002u : 0x4b575450u;
    for(;;) __asm__ volatile("nop");
}
