#include "kwt.h"

// Dedicated regression firmware: A, B, poison/abort, timeout, recovery A.
// Source images are prepared in ITCM before boot. All task transfers and
// computation still use actual CPU accesses to shared SRAM and the accelerator.
static volatile uint32_t *const mail=(volatile uint32_t *)(uintptr_t)0xa001f000u;
static inline void barrier(void) { __asm__ volatile("fence iorw,iorw" ::: "memory"); }
static inline uint32_t reg_read(unsigned offset) { return *(volatile uint32_t *)(uintptr_t)(KWT_BASE+offset); }
static inline void reg_write(unsigned offset,uint32_t value) { *(volatile uint32_t *)(uintptr_t)(KWT_BASE+offset)=value; }
static uint64_t cycles(void) {
    uint32_t hi,lo,again;
    do { __asm__ volatile("csrr %0,mcycleh":"=r"(hi));
         __asm__ volatile("csrr %0,mcycle":"=r"(lo));
         __asm__ volatile("csrr %0,mcycleh":"=r"(again)); } while(hi!=again);
    return ((uint64_t)hi<<32)|lo;
}
static void fail(uint32_t reason) {
    mail[1]=reason;barrier();mail[0]=0xbad00003u;
    for(;;)__asm__ volatile("nop");
}
static void phase(uint32_t marker) { mail[10]=marker;barrier(); }
static void task(const volatile uint16_t *source,unsigned shift,unsigned index) {
    volatile uint16_t *input=(volatile uint16_t *)(uintptr_t)KWT_SHARED_BASE;
    volatile int16_t *output=(volatile int16_t *)(uintptr_t)0xa000c000u;
    struct kwt_stats stats;
    mail[0]=0;kwt_abort();
    uint64_t begin=cycles();
    mail[8]=0x4b575442u;barrier();
    for(unsigned i=0;i<KWT_LOAD_WORDS;i++) input[i]=source[i];
    barrier();
    int rc=kwt_run_layer(input,output,shift,100000000u,&stats);
    uint64_t elapsed=cycles()-begin;
    if(rc!=KWT_OK)fail((uint32_t)rc);
    mail[1]=0;mail[2]=stats.input_words;mail[3]=stats.output_words;
    mail[4]=(uint32_t)elapsed;mail[5]=(uint32_t)(elapsed>>32);
    mail[6]=stats.saturated;mail[7]=index;
    barrier();mail[0]=0x4b575450u;barrier();
}
int main(void) {
    const volatile uint16_t *first=(const volatile uint16_t *)(uintptr_t)0x80010000u;
    const volatile uint16_t *second=(const volatile uint16_t *)(uintptr_t)0x80020000u;
    const volatile uint32_t *metadata=(const volatile uint32_t *)(uintptr_t)0x8000fff0u;
    task(first,metadata[0],1);
    task(second,metadata[1],2);

    kwt_abort();
    phase(0x504f4931u); // POI1: observer arms partial-load poison checks.
    reg_write(KWT_SHIFT,31);reg_write(KWT_CONTROL,1);barrier();
    for(unsigned i=0;i<17;i++) {
        if(!(reg_read(KWT_STATUS)&2u))fail(0x301u);
        reg_write(KWT_LOAD,(i^0x5a5au)&65535u);
    }
    barrier();
    if(reg_read(KWT_LOAD_COUNT)!=17u || reg_read(KWT_OUTPUT_COUNT))fail(0x305u);
    kwt_abort();
    if((reg_read(KWT_STATUS)&29u) || reg_read(KWT_LOAD_COUNT) || reg_read(KWT_OUTPUT_COUNT))fail(0x302u);
    phase(0x504f4932u); // POI2: poison aborted and counters invalidated.

    phase(0x54494d31u); // TIM1: actual driver must hit its cycle timeout.
    struct kwt_stats stats;
    int rc=kwt_run_layer((const volatile uint16_t *)(uintptr_t)KWT_SHARED_BASE,
                        (volatile int16_t *)(uintptr_t)0xa000c000u,metadata[1],1u,&stats);
    if(rc!=KWT_TIMEOUT)fail(0x303u);
    if((reg_read(KWT_STATUS)&29u) || reg_read(KWT_LOAD_COUNT) || reg_read(KWT_OUTPUT_COUNT))fail(0x304u);
    mail[11]=(uint32_t)rc;phase(0x54494d32u); // TIM2: reset/recovery observed.

    task(first,metadata[0],3);
    for(;;)__asm__ volatile("nop");
}
