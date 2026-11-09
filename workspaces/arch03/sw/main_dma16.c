#include "kwt_dma16.h"
#ifndef KWT_DMA16_DEFAULT_MODE
#define KWT_DMA16_DEFAULT_MODE 1u
#endif
#ifndef KWT_DMA16_DEFAULT_PREFETCH
#define KWT_DMA16_DEFAULT_PREFETCH 1u
#endif
#ifndef KWT_DMA16_TIMEOUT_CYCLES
#define KWT_DMA16_TIMEOUT_CYCLES 100000000ull
#endif
#ifndef KWT_DMA16_CANCEL_TIMEOUT_CYCLES
#define KWT_DMA16_CANCEL_TIMEOUT_CYCLES 1000000ull
#endif
int main(void) {
    volatile uint32_t *mail=(volatile uint32_t *)(uintptr_t)0xa001f000u;
    const volatile uint32_t *metadata=(const volatile uint32_t *)(uintptr_t)0x8000fff0u;
    struct kwt_dma16_config cfg;
    struct kwt_dma16_stats stats;
    cfg.source=KWT_DMA16_SOURCE;cfg.input=KWT_DMA16_INPUT;cfg.output=KWT_DMA16_OUTPUT;
    cfg.shift=metadata[0];cfg.dma_mode=KWT_DMA16_DEFAULT_MODE;cfg.prefetch=KWT_DMA16_DEFAULT_PREFETCH;
    mail[0]=0;
    int rc=kwt_dma16_run(&cfg,KWT_DMA16_TIMEOUT_CYCLES,KWT_DMA16_CANCEL_TIMEOUT_CYCLES,&stats);
    /* Existing completion fields retained. Firmware cycles are diagnostic;
     * official task time comes from the passive first-request/last-ACK window. */
    mail[1]=(uint32_t)rc;mail[2]=stats.input_words;mail[3]=stats.output_words;
    mail[4]=(uint32_t)stats.cycles;mail[5]=(uint32_t)(stats.cycles>>32);mail[6]=stats.saturated;
    mail[7]=KWT_DMA16_ID_VALUE;mail[8]=KWT_DMA16_LAYOUT;
    mail[9]=stats.status;mail[10]=stats.completion;mail[11]=stats.pending;
    mail[12]=stats.first_error;mail[13]=stats.error_addr;mail[14]=stats.error_phase;
    mail[15]=stats.source_acks;mail[16]=stats.stage_acks;mail[17]=stats.load_acks;mail[18]=stats.output_acks;
    mail[19]=stats.load_committed;mail[20]=stats.output_committed;mail[21]=stats.irq_events;
    mail[22]=stats.external_irqs;mail[23]=stats.timer_irqs;mail[24]=stats.wfi_count;
    mail[25]=stats.unhandled_irqs;mail[26]=stats.last_mcause;mail[27]=stats.cancel_drained;
    mail[28]=cfg.dma_mode|(cfg.prefetch<<1);mail[29]=(uint32_t)stats.primary_result;
    mail[30]=KWT_DMA16_USE_IRQ;mail[31]=cfg.source;
    __asm__ volatile("fence iorw,iorw" ::: "memory");
    mail[0]=rc ? 0xbad00002u : 0x4b575450u;
    for(;;) __asm__ volatile("nop");
}
