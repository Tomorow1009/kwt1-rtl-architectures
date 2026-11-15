/* Separate CPU/shared-SRAM stress firmware. Not the IRQ performance image.
 * Task inputs still arrive solely through the original SysMem DMA path.
 * Scratch lies outside task input/output and the completion mailbox. */
#include "kwt_t64.h"
#if KWT_ICB32_ROWS != 4u
#error "T64 contention firmware requires four rows"
#endif
#define SCRATCH_BASE 0xa0040000u
#define TIMEOUT 100000000ull
static uint32_t rd(unsigned offset) {
    return *(volatile uint32_t *)(uintptr_t)(KWT_ICB32_BASE+offset);
}
static void wr(unsigned offset,uint32_t value) {
    *(volatile uint32_t *)(uintptr_t)(KWT_ICB32_BASE+offset)=value;
}
static void fence(void) { __asm__ volatile("fence iorw,iorw" ::: "memory"); }
static int ready(uint64_t start) {
    while(!(rd(K16_STATUS)&0x4000u)) {
        if(rd(K16_STATUS)&16u) return K16_DEVICE_ERROR;
        if(kwt_icb32_cycles()-start>=TIMEOUT) return K16_TIMEOUT;
    }
    return K16_OK;
}
int main(void) {
    volatile uint32_t *mail=(volatile uint32_t *)(uintptr_t)0xa001f000u;
    volatile uint32_t *scratch=(volatile uint32_t *)(uintptr_t)SCRATCH_BASE;
    const volatile uint32_t *metadata=(const volatile uint32_t *)(uintptr_t)0x8000fff0u;
    struct kwt_icb32_stats s;
    volatile unsigned char *zero=(volatile unsigned char *)&s;
    for(unsigned i=0;i<sizeof(s);i++) zero[i]=0;
    mail[0]=0;
    uint32_t rounds=0;
    uint64_t start=kwt_icb32_cycles();
    int rc=rd(K16_ID)==KWT_ICB32_ID_VALUE ? K16_OK : K16_BAD_ID;
    if(!rc && (rd(K16_CAPABILITY)!=KWT_T64_CAPABILITY ||
       rd(K16_NUMERIC_FORMAT)!=KWT_T64_NUMERIC_FORMAT)) rc=K16_BAD_ID;
    if(!rc && (metadata[0]!=10u || metadata[2]!=KWT_ICB32_LAYOUT || metadata[3]!=KWT_ICB32_ROWS ||
       metadata[1]<32u || metadata[1]>KWT_ICB32_MAX_INPUT_BYTES || (metadata[1]&3u))) rc=K16_BAD_ARGUMENT;
    if(!rc) { wr(K16_IRQ_ENABLE,0);rc=kwt_icb32_cancel(1000000ull,&s); }
    if(!rc) { wr(K16_CONTROL,4);fence();rc=ready(start); }
    if(!rc) {
        wr(K16_SHIFT,metadata[0]);wr(K16_MODE,3);
        wr(K16_SOURCE_BASE,KWT_ICB32_SOURCE);wr(K16_INPUT_BASE,KWT_ICB32_INPUT);
        wr(K16_OUTPUT_BASE,KWT_ICB32_OUTPUT);wr(K16_INPUT_BYTES,metadata[1]);
        wr(K16_OUTPUT_BYTES,KWT_ICB32_OUTPUT_BYTES);wr(K16_LAYOUT,metadata[2]);
        fence();wr(K16_CONTROL,1);fence();
    }
    while(!rc) {
        uint32_t status=rd(K16_STATUS);
        if(status&16u) { rc=K16_DEVICE_ERROR;break; }
        if(status&8u) break;
        /* Actual volatile writes/reads compete for the SAME ICB arbiter.
         * Check every word, never read uninitialized scratch or task data. */
        for(unsigned i=0;i<32;i++) {
            uint32_t expected=0x5a69c300u^(rounds*33u+i);
            scratch[i]=expected;
            fence();
            if(scratch[i]!=expected) { rc=K16_BAD_OUTPUT;break; }
        }
        rounds++;
        if(kwt_icb32_cycles()-start>=TIMEOUT) rc=K16_TIMEOUT;
    }
    fence();kwt_icb32_snapshot(&s);
    if(!rc && (rounds<1 || s.input_words!=23488 || s.output_words!=25344 ||
       !(s.status&8u) || (s.completion&31u)!=31u || (s.pending&0x00003f1fu) ||
       s.load_committed!=metadata[1] || s.output_committed!=50688 || s.first_error ||
       s.source_acks!=metadata[1]/4u || s.stage_acks!=metadata[1]/4u || s.load_acks!=metadata[1]/4u ||
       s.output_acks!=12672)) rc=K16_BAD_OUTPUT;
    s.primary_result=rc;
    if(rc && kwt_icb32_cancel(1000000ull,&s)!=K16_OK) rc=K16_NOT_DRAINED;
    s.cycles=kwt_icb32_cycles()-start;
    mail[1]=(uint32_t)rc;mail[2]=s.input_words;mail[3]=s.output_words;
    mail[4]=(uint32_t)s.cycles;mail[5]=(uint32_t)(s.cycles>>32);mail[6]=s.saturated;
    mail[7]=KWT_ICB32_ID_VALUE;mail[8]=metadata[2];
    mail[9]=s.status;mail[10]=s.completion;mail[11]=s.pending;
    mail[12]=s.first_error;mail[13]=s.error_addr;mail[14]=s.error_phase;
    mail[15]=s.source_acks;mail[16]=s.stage_acks;mail[17]=s.load_acks;mail[18]=s.output_acks;
    mail[19]=s.load_committed;mail[20]=s.output_committed;
    mail[21]=0;mail[22]=0;mail[23]=0;mail[24]=0;mail[25]=s.unhandled_irqs;
    mail[26]=s.last_mcause;mail[27]=s.cancel_drained;
    mail[28]=rounds;mail[29]=(uint32_t)s.primary_result;mail[30]=0;mail[31]=KWT_ICB32_SOURCE;
    mail[32]=metadata[1];mail[33]=KWT_ICB32_ROWS;
    fence();mail[0]=rc ? 0xbad00002u : 0x4b575450u;
    for(;;) __asm__ volatile("nop");
}
