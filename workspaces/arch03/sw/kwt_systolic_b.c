#include "kwt_systolic_b.h"

#define MSTATUS_MIE 8u
#define MIE_MTIE 0x80u
#define MIE_MEIE 0x800u
#define STATUS_BUSY 1u
#define STATUS_DONE 8u
#define STATUS_ERROR 16u
#define STATUS_START_READY 0x4000u
/* PENDING kind/state fields are diagnostics, not outstanding work. */
#define PENDING_VALID_MASK 0x00003f1fu
static volatile uint32_t irq_events, external_irqs, timer_irqs, wfi_count;
static volatile uint32_t unhandled_irqs, last_mcause, irq_fault;

static inline uint32_t mmio_read(uint32_t address) {
    return *(volatile uint32_t *)(uintptr_t)address;
}
static inline void mmio_write(uint32_t address, uint32_t value) {
    *(volatile uint32_t *)(uintptr_t)address=value;
}
static inline uint32_t reg_read(uint32_t offset) { return mmio_read(KWT_ICB32_BASE+offset); }
static inline void reg_write(uint32_t offset,uint32_t value) { mmio_write(KWT_ICB32_BASE+offset,value); }
static inline void fence_io(void) { __asm__ volatile("fence iorw,iorw" ::: "memory"); }
uint64_t kwt_icb32_cycles(void) {
    uint32_t hi,lo,again;
    do {
        __asm__ volatile("csrr %0,mcycleh":"=r"(hi));
        __asm__ volatile("csrr %0,mcycle":"=r"(lo));
        __asm__ volatile("csrr %0,mcycleh":"=r"(again));
    } while(hi!=again);
    return ((uint64_t)hi<<32)|lo;
}
static void zero_stats(struct kwt_icb32_stats *stats) {
    volatile unsigned char *bytes=(volatile unsigned char *)stats;
    for(unsigned i=0;i<sizeof(*stats);i++) bytes[i]=0;
}
void kwt_icb32_snapshot(struct kwt_icb32_stats *s) {
    if(!s) return;
    s->input_words=reg_read(K16_LOAD_COUNT);s->output_words=reg_read(K16_OUTPUT_COUNT);
    s->saturated=reg_read(K16_SAT_COUNT);s->status=reg_read(K16_STATUS);
    s->completion=reg_read(K16_COMPLETION);s->pending=reg_read(K16_PENDING);
    s->first_error=reg_read(K16_FIRST_ERROR);s->error_addr=reg_read(K16_FIRST_ERROR_ADDR);
    s->error_phase=reg_read(K16_FIRST_ERROR_PHASE);s->load_committed=reg_read(K16_LOAD_COMMITTED);
    s->output_committed=reg_read(K16_OUTPUT_COMMITTED);s->source_acks=reg_read(K16_SOURCE_ACKS);
    s->stage_acks=reg_read(K16_STAGE_ACKS);s->load_acks=reg_read(K16_LOAD_ACKS);
    s->output_acks=reg_read(K16_OUTPUT_ACKS);s->irq_events=irq_events;
    s->external_irqs=external_irqs;s->timer_irqs=timer_irqs;s->wfi_count=wfi_count;
    s->unhandled_irqs=unhandled_irqs;s->last_mcause=last_mcause;
}
int kwt_icb32_cancel(uint64_t timeout,struct kwt_icb32_stats *s) {
    if(!timeout) return K16_BAD_ARGUMENT;
    uint64_t start=kwt_icb32_cycles();
    reg_write(K16_CONTROL,2);fence_io();
    for(;;) {
        uint32_t status=reg_read(K16_STATUS),completion=reg_read(K16_COMPLETION);
        uint32_t pending=reg_read(K16_PENDING);
        if((status&STATUS_START_READY) && !(status&(STATUS_BUSY|0x20u|0x80u|0x100u|0x2000u)) &&
           (completion&0x30u)==0x30u && !(pending&PENDING_VALID_MASK)) {
            kwt_icb32_snapshot(s);if(s) s->cancel_drained=1;return K16_OK;
        }
        if(kwt_icb32_cycles()-start>=timeout) {
            kwt_icb32_snapshot(s);if(s) s->cancel_drained=0;return K16_NOT_DRAINED;
        }
    }
}

static int wait_start_ready(uint64_t start,uint64_t timeout) {
    for(;;) {
        uint32_t status=reg_read(K16_STATUS);
        if(status&STATUS_ERROR) return K16_DEVICE_ERROR;
        if(!(status&STATUS_BUSY) && (status&STATUS_START_READY)) return K16_OK;
        if(kwt_icb32_cycles()-start>=timeout) return K16_TIMEOUT;
    }
}

__attribute__((weak)) int kwt_icb32_shared_irq_hook(uint32_t claim) {
    (void)claim;return 0;
}

#if KWT_ICB32_USE_IRQ
static uint32_t saved_mstatus,saved_mie,saved_enable,saved_priority,saved_threshold;
static uint64_t saved_compare;
static uint64_t timer_read(uint32_t address) {
    uint32_t hi,lo,again;
    do { hi=mmio_read(address+4);lo=mmio_read(address);again=mmio_read(address+4); } while(hi!=again);
    return ((uint64_t)hi<<32)|lo;
}
static void timer_write_compare(uint64_t value) {
    /* RV32 safe compare update: prevent a transient earlier deadline. */
    mmio_write(KWT_MTIMECMP_ADDR+4,0xffffffffu);
    mmio_write(KWT_MTIMECMP_ADDR,(uint32_t)value);
    mmio_write(KWT_MTIMECMP_ADDR+4,(uint32_t)(value>>32));fence_io();
}
static void timer_arm(void) { timer_write_compare(timer_read(KWT_MTIME_ADDR)+(uint64_t)KWT_TIMER_WAKE_TICKS); }
static void irq_shutdown(void) {
    __asm__ volatile("csrci mstatus,8" ::: "memory");
    __asm__ volatile("csrc mie,%0" :: "r"(MIE_MTIE|MIE_MEIE) : "memory");
    reg_write(K16_IRQ_ENABLE,0);fence_io();
    timer_write_compare(saved_compare);
    mmio_write(KWT_PLIC_ENABLE_ADDR,saved_enable);
    mmio_write(KWT_PLIC_PRIORITY_ADDR,saved_priority);
    mmio_write(KWT_PLIC_THRESHOLD_ADDR,saved_threshold);fence_io();
    __asm__ volatile("csrw mie,%0" :: "r"(saved_mie) : "memory");
    __asm__ volatile("csrw mstatus,%0" :: "r"(saved_mstatus) : "memory");
}
static int irq_setup(void) {
    __asm__ volatile("csrrc %0,mstatus,%1" : "=r"(saved_mstatus) : "r"(MSTATUS_MIE) : "memory");
    __asm__ volatile("csrr %0,mie" : "=r"(saved_mie));
    saved_enable=mmio_read(KWT_PLIC_ENABLE_ADDR);saved_priority=mmio_read(KWT_PLIC_PRIORITY_ADDR);
    saved_threshold=mmio_read(KWT_PLIC_THRESHOLD_ADDR);saved_compare=timer_read(KWT_MTIMECMP_ADDR);
    mmio_write(KWT_PLIC_PRIORITY_ADDR,1);mmio_write(KWT_PLIC_THRESHOLD_ADDR,0);
    mmio_write(KWT_PLIC_ENABLE_ADDR,saved_enable|KWT_PLIC_ENABLE_MASK);
    reg_write(K16_IRQ_STATUS,7);reg_write(K16_IRQ_ENABLE,7);timer_arm();fence_io();
    __asm__ volatile("csrs mie,%0" :: "r"(MIE_MTIE|MIE_MEIE) : "memory");
    __asm__ volatile("csrsi mstatus,8" ::: "memory");
    /* Before ever sleeping, require a real timer interrupt to execute. A
     * wrong timer route cannot silently turn a finite timeout into a hang. */
    uint64_t start=kwt_icb32_cycles();
    while(timer_irqs==0) {
        if(irq_fault || kwt_icb32_cycles()-start>=(uint64_t)KWT_TIMER_PROBE_CYCLES) {
            irq_shutdown();return K16_TIMER_NOT_VERIFIED;
        }
    }
    return K16_OK;
}
static void wait_interrupt(uint64_t start,uint64_t timeout) {
    uint32_t previous;
    __asm__ volatile("csrrc %0,mstatus,%1" : "=r"(previous) : "r"(MSTATUS_MIE) : "memory");
    uint32_t status=reg_read(K16_STATUS);
    if(!(status&(STATUS_DONE|STATUS_ERROR|0x40u)) && !irq_fault && kwt_icb32_cycles()-start<timeout) {
        /* Locally enabled MTIE/MEIE wake WFI with global MIE clear. A pending
         * event cannot be serviced between this check and WFI. The periodic
         * timer remains armed even if the DMA completion IRQ never arrives. */
        wfi_count++;__asm__ volatile("wfi" ::: "memory");
    }
    if(previous&MSTATUS_MIE) __asm__ volatile("csrsi mstatus,8" ::: "memory");
}
#endif

void kwt_icb32_trap(uint32_t cause,uint32_t epc,uint32_t value) {
    last_mcause=cause;
#if KWT_ICB32_USE_IRQ
    if(cause==0x80000007u) { timer_irqs++;timer_arm();return; }
    if(cause==0x8000000bu) {
        external_irqs++;
        for(unsigned count=0;count<16;count++) {
            uint32_t claim=mmio_read(KWT_PLIC_CLAIM_ADDR);
            if(!claim) return;
            uint32_t events=claim==KWT_DMA_IRQ_ID ? reg_read(K16_IRQ_STATUS)&7u : 0;
            int handled=0;
            if(events) { irq_events|=events;reg_write(K16_IRQ_STATUS,events);fence_io();handled=1; }
            if(!handled) handled=kwt_icb32_shared_irq_hook(claim);
            mmio_write(KWT_PLIC_CLAIM_ADDR,claim);fence_io();
            if(!handled) {
                unhandled_irqs++;irq_fault=1;
                __asm__ volatile("csrc mie,%0" :: "r"(MIE_MEIE) : "memory");
                return;
            }
        }
        unhandled_irqs++;irq_fault=1;
        __asm__ volatile("csrc mie,%0" :: "r"(MIE_MEIE) : "memory");
        return;
    }
#endif
    volatile uint32_t *mail=(volatile uint32_t *)(uintptr_t)0xa001f000u;
    mail[1]=cause;mail[2]=epc;mail[3]=value;fence_io();mail[0]=0xbad00001u;
    for(;;) __asm__ volatile("nop");
}

static int valid_config(const struct kwt_icb32_config *c) {
    if(!c || c->shift>31 || c->dma_mode!=1 || c->encoded_bytes<32 || c->encoded_bytes>KWT_ICB32_MAX_INPUT_BYTES || (c->encoded_bytes&3u) || c->prefetch>1 || ((c->source|c->input|c->output)&3u)) return 0;
    if(c->layout!=KWT_ICB32_LAYOUT && c->layout!=KWT_SYSTOLIC_LAYOUT_V3) return 0;
    uint64_t se=(uint64_t)c->source+c->encoded_bytes;
    uint64_t ie=(uint64_t)c->input+c->encoded_bytes,oe=(uint64_t)c->output+KWT_ICB32_OUTPUT_BYTES;
    return c->source>=0xb0000000u && se<=0xb000c000ull && c->input>=KWT_ICB32_INPUT && c->output>=KWT_ICB32_INPUT &&
        ie<=((uint64_t)KWT_ICB32_INPUT+KWT_ICB32_SHARED_BYTES) && oe<=((uint64_t)KWT_ICB32_INPUT+KWT_ICB32_SHARED_BYTES) &&
        (ie<=c->output || oe<=c->input) && (se<=c->input || c->source>=ie) && (se<=c->output || c->source>=oe);
}
int kwt_icb32_run(const struct kwt_icb32_config *c,uint64_t timeout,uint64_t cancel_timeout,struct kwt_icb32_stats *s) {
    if(!s) return K16_BAD_ARGUMENT;
    zero_stats(s);
    if(!valid_config(c) || !timeout || !cancel_timeout) { s->primary_result=K16_BAD_ARGUMENT;return K16_BAD_ARGUMENT; }
    irq_events=external_irqs=timer_irqs=wfi_count=unhandled_irqs=last_mcause=irq_fault=0;
    uint64_t start=kwt_icb32_cycles();
    if(reg_read(K16_ID)!=KWT_ICB32_ID_VALUE) { s->primary_result=K16_BAD_ID;return K16_BAD_ID; }
    reg_write(K16_IRQ_ENABLE,0);
    int rc=kwt_icb32_cancel(cancel_timeout,s);
    if(rc) { s->primary_result=rc;s->cycles=kwt_icb32_cycles()-start;return rc; }
    reg_write(K16_CONTROL,4);fence_io();
    /* CLEAR initiates another core invalidation/flush. This must finish
     * before either a debug source copy or START can expose the next task. */
    rc=wait_start_ready(start,timeout);
    if(rc) {
        s->primary_result=rc;
        if(kwt_icb32_cancel(cancel_timeout,s)!=K16_OK) rc=K16_NOT_DRAINED;
        s->cycles=kwt_icb32_cycles()-start;return rc;
    }
    reg_write(K16_SHIFT,c->shift);reg_write(K16_MODE,c->dma_mode|(c->prefetch<<1));
    reg_write(K16_SOURCE_BASE,c->source);reg_write(K16_INPUT_BASE,c->input);reg_write(K16_OUTPUT_BASE,c->output);
    reg_write(K16_INPUT_BYTES,c->encoded_bytes);reg_write(K16_OUTPUT_BYTES,KWT_ICB32_OUTPUT_BYTES);
    reg_write(K16_LAYOUT,c->layout);fence_io();
#if KWT_ICB32_USE_IRQ
    if(c->dma_mode) {
        rc=irq_setup();
        if(rc) { kwt_icb32_snapshot(s);s->primary_result=rc;s->cycles=kwt_icb32_cycles()-start;return rc; }
    }
#endif
    if(!rc) rc=wait_start_ready(start,timeout);
    if(!rc) { reg_write(K16_CONTROL,1);fence_io(); }
    while(!rc) {
        uint32_t status=reg_read(K16_STATUS);
        if(status&STATUS_ERROR) { rc=K16_DEVICE_ERROR;break; }
        if(irq_fault) { rc=K16_UNHANDLED_IRQ;break; }
        if(status&STATUS_DONE) break;
        if(kwt_icb32_cycles()-start>=timeout) { rc=K16_TIMEOUT;break; }
#if KWT_ICB32_USE_IRQ
        if(c->dma_mode) wait_interrupt(start,timeout);
#endif
    }
    fence_io();kwt_icb32_snapshot(s);
    if(!rc && (s->input_words!=23488 || s->output_words!=25344 || !(s->status&STATUS_DONE))) rc=K16_BAD_OUTPUT;
    if(!rc && c->dma_mode && ((s->completion&31u)!=31u || (s->pending&PENDING_VALID_MASK) ||
        s->load_committed!=c->encoded_bytes || s->output_committed!=50688 ||
        s->source_acks!=c->encoded_bytes/4 || s->stage_acks!=c->encoded_bytes/4 || s->load_acks!=0 || s->output_acks!=12672)) rc=K16_BAD_OUTPUT;
    s->primary_result=rc;
    if(rc && kwt_icb32_cancel(cancel_timeout,s)!=K16_OK) rc=K16_NOT_DRAINED;
#if KWT_ICB32_USE_IRQ
    if(c->dma_mode) irq_shutdown();
#endif
    s->cycles=kwt_icb32_cycles()-start;
    return rc;
}
