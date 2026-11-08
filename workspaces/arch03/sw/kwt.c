#include "kwt.h"
static inline uint32_t read_reg(unsigned off) { return *(volatile uint32_t *)(uintptr_t)(KWT_BASE+off); }
static inline void write_reg(unsigned off,uint32_t v) { *(volatile uint32_t *)(uintptr_t)(KWT_BASE+off)=v; }
static inline void fence_io(void) { __asm__ volatile("fence iorw,iorw" ::: "memory"); }
static uint64_t cycles(void) {
    uint32_t hi,lo,again;
    do { __asm__ volatile("csrr %0,mcycleh":"=r"(hi));
         __asm__ volatile("csrr %0,mcycle":"=r"(lo));
         __asm__ volatile("csrr %0,mcycleh":"=r"(again)); } while(hi!=again);
    return ((uint64_t)hi<<32)|lo;
}
void kwt_abort(void) { write_reg(KWT_CONTROL,2);fence_io(); }
static int buffer_ok(uintptr_t p,uint32_t bytes) {
    return !(p&1) && p>=KWT_SHARED_BASE && p<=KWT_SHARED_BASE+KWT_SHARED_BYTES-bytes;
}
int kwt_run_layer(const volatile uint16_t *load,volatile int16_t *output,
    unsigned shift,uint64_t timeout_cycles,struct kwt_stats *stats) {
    uintptr_t a=(uintptr_t)load,b=(uintptr_t)output;
    uint32_t sent=0,received=0,saturated=0;
    uint32_t expected_row=0,expected_col=0;
    uint64_t start;
    if(!stats || shift>31 || !timeout_cycles || !buffer_ok(a,2*KWT_LOAD_WORDS) ||
       !buffer_ok(b,2*KWT_OUTPUT_WORDS) ||
       !(a+2*KWT_LOAD_WORDS<=b || b+2*KWT_OUTPUT_WORDS<=a)) return KWT_BAD_ARGUMENT;
    stats->cycles=0;stats->input_words=0;stats->output_words=0;stats->saturated=0;
    kwt_abort(); // invalidate previous task; SRAM contents need not be physically cleared.
    if(read_reg(KWT_ID)!=0x4b575403u) return KWT_DEVICE_ERROR;
    write_reg(KWT_SHIFT,shift);fence_io();
    start=cycles(); // includes start, all input loads, polls, computation and final SRAM writes.
    write_reg(KWT_CONTROL,1);
    for(;;) {
        uint32_t status=read_reg(KWT_STATUS);
        if(status&16u) { kwt_abort();return KWT_DEVICE_ERROR; }
        if((status&2u) && sent<KWT_LOAD_WORDS) write_reg(KWT_LOAD,load[sent++]);
        if(status&4u) {
            uint32_t word=read_reg(KWT_OUTPUT);
            uint32_t row=(word>>16)&127u,col=(word>>23)&255u;
            // Exact group -> row -> lane sequence; detects duplicate/missing coordinates.
            // Advance only after a checked output. Avoid /792 and %792 in the
            // per-output path without weakening the exact coordinate check.
            if(received>=KWT_OUTPUT_WORDS || row!=expected_row || col!=expected_col) {
                kwt_abort();return KWT_BAD_OUTPUT;
            }
            output[row*256u+col]=(int16_t)(word&65535u);
            saturated+=word>>31;received++;
            if((expected_col&7u)!=7u) {
                expected_col++;
            } else if(expected_row!=98u) {
                expected_row++;expected_col-=7u;
            } else {
                expected_row=0;expected_col++;
            }
        }
        if((status&8u) && received==KWT_OUTPUT_WORDS) break;
        if(cycles()-start>=timeout_cycles) { kwt_abort();return KWT_TIMEOUT; }
    }
    fence_io();stats->cycles=cycles()-start;
    stats->input_words=sent;stats->output_words=received;stats->saturated=saturated;
    if(sent!=KWT_LOAD_WORDS || read_reg(KWT_LOAD_COUNT)!=sent || read_reg(KWT_OUTPUT_COUNT)!=received)
        return KWT_DEVICE_ERROR;
    return KWT_OK;
}
