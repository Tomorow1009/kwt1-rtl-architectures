#include "kwt_p80.h"
#if KWT_ICB32_USE_IRQ
#error "This first sequence firmware is polling-only; IRQ requires separate evidence"
#endif
#ifndef KWT_SEQUENCE_TIMEOUT_CYCLES
#define KWT_SEQUENCE_TIMEOUT_CYCLES 100000000ull
#endif
#ifndef KWT_SEQUENCE_CANCEL_TIMEOUT_CYCLES
#define KWT_SEQUENCE_CANCEL_TIMEOUT_CYCLES 1000000ull
#endif
#define SEQUENCE_MAGIC 0x54385351u
#define SEQUENCE_PASS 0x54385350u
#define PENDING_MASK 0x3f1fu

static volatile uint32_t expected_fault, fault_seen, trap_count;
static volatile uint32_t trap_cause, trap_epc, trap_value;
extern void sequence_guarded_start(void);
extern unsigned char sequence_fault_store[], sequence_fault_resume[];

static inline uint32_t read_reg(uint32_t off) {
    return *(volatile uint32_t *)(uintptr_t)(KWT_ICB32_BASE+off);
}
static inline void write_reg(uint32_t off, uint32_t value) {
    *(volatile uint32_t *)(uintptr_t)(KWT_ICB32_BASE+off)=value;
}
static inline void fence_io(void) {
    __asm__ volatile("fence iorw,iorw" ::: "memory");
}
static void clear_stats(struct kwt_icb32_stats *stats) {
    volatile unsigned char *p=(volatile unsigned char *)stats;
    for(unsigned i=0;i<sizeof(*stats);i++)p[i]=0;
}

/* Only the exact deliberately rejected START store is recoverable. Its actual
 * machine exception supplies all trap evidence; no fault is synthesized. */
uint32_t icb32_sequence_trap(uint32_t cause,uint32_t epc,uint32_t value) {
    if(expected_fault && cause==7u && epc==(uint32_t)(uintptr_t)sequence_fault_store &&
       value==KWT_ICB32_BASE+K16_CONTROL) {
        expected_fault=0;fault_seen=1;trap_count++;
        trap_cause=cause;trap_epc=epc;trap_value=value;
        return (uint32_t)(uintptr_t)sequence_fault_resume;
    }
    kwt_icb32_trap(cause,epc,value);
    for(;;)__asm__ volatile("nop");
}

static int ready_and_drained(void) {
    uint32_t status=read_reg(K16_STATUS);
    return (status&0x4000u) && !(status&0x39a1u) && !(read_reg(K16_PENDING)&PENDING_MASK);
}

static int prepare_idle(struct kwt_icb32_stats *stats) {
    if(read_reg(K16_TRANSACTION_DEPTH)!=KWT_P80_TRANSACTION_DEPTH ||
       read_reg(K16_ID)!=KWT_ICB32_ID_VALUE ||
       read_reg(K16_CAPABILITY)!=KWT_P80_CAPABILITY ||
       read_reg(K16_NUMERIC_FORMAT)!=KWT_P80_NUMERIC_FORMAT)return K16_BAD_ID;
    write_reg(K16_IRQ_ENABLE,0);
    int rc=kwt_icb32_cancel(KWT_SEQUENCE_CANCEL_TIMEOUT_CYCLES,stats);
    if(rc)return rc;
    write_reg(K16_CONTROL,4);fence_io();
    uint64_t start=kwt_icb32_cycles();
    for(;;) {
        if(read_reg(K16_STATUS)&16u)return K16_DEVICE_ERROR;
        if(ready_and_drained())return K16_OK;
        if(kwt_icb32_cycles()-start>=KWT_SEQUENCE_CANCEL_TIMEOUT_CYCLES)return K16_NOT_DRAINED;
    }
}

static void configure(uint32_t descriptor) {
    write_reg(K16_SHIFT,descriptor&31u);write_reg(K16_MODE,3);
    write_reg(K16_SOURCE_BASE,KWT_ICB32_SOURCE);write_reg(K16_INPUT_BASE,KWT_ICB32_INPUT);
    write_reg(K16_OUTPUT_BASE,KWT_ICB32_OUTPUT);write_reg(K16_INPUT_BYTES,((descriptor>>17)*4u));
    write_reg(K16_OUTPUT_BYTES,KWT_ICB32_OUTPUT_BYTES);write_reg(K16_LAYOUT,KWT_ICB32_LAYOUT);
    fence_io();
}

static int phase_begin(uint32_t phase,uint32_t descriptor) {
    if(!ready_and_drained())return K16_NOT_DRAINED;
    volatile uint32_t *mail=(volatile uint32_t *)(uintptr_t)0xa001f000u;
    /* A source-model selector only; this write must not transfer task data.
     * The observer switches bank after the successful mailbox write ACK. */
    mail[33]=descriptor;fence_io();
    mail[32]=phase;fence_io();
    return K16_OK;
}

static void receipt(uint32_t phase,uint32_t kind,int rc,uint32_t descriptor,
                    uint32_t bad_offset,uint32_t bad_value,uint32_t timeout,
                    uint32_t before_source,uint32_t before_stage,uint32_t before_status,
                    const struct kwt_icb32_stats *s) {
    volatile uint32_t *r=(volatile uint32_t *)(uintptr_t)(0xa0020000u+(phase-1u)*0x100u);
    volatile uint32_t *mail=(volatile uint32_t *)(uintptr_t)0xa001f000u;
    r[0]=phase;r[1]=kind;r[2]=(uint32_t)rc;r[3]=s->status;r[4]=s->completion;r[5]=s->pending;
    r[6]=s->first_error;r[7]=s->error_addr;r[8]=s->error_phase;
    r[9]=s->source_acks;r[10]=s->stage_acks;r[11]=s->load_acks;r[12]=s->output_acks;
    r[13]=s->load_committed;r[14]=s->output_committed;r[15]=s->input_words;r[16]=s->output_words;
    r[17]=s->saturated;r[18]=(uint32_t)s->cycles;r[19]=(uint32_t)(s->cycles>>32);
    r[20]=s->cancel_drained;r[21]=trap_count;r[22]=trap_cause;r[23]=trap_epc;r[24]=trap_value;
    r[25]=descriptor;r[26]=bad_offset;r[27]=bad_value;r[28]=timeout;
    r[29]=before_source;r[30]=before_stage;r[31]=before_status;r[32]=(uint32_t)s->primary_result;
    fence_io();mail[34]=phase;fence_io();
}

static int rejected_configuration(uint32_t off,uint32_t value,struct kwt_icb32_stats *stats) {
    uint32_t prior=trap_count;
    uint64_t start=kwt_icb32_cycles();
    write_reg(off,value);fence_io();
    fault_seen=0;expected_fault=1;fence_io();
    sequence_guarded_start();
    expected_fault=0;
    int rc=kwt_icb32_cancel(KWT_SEQUENCE_CANCEL_TIMEOUT_CYCLES,stats);
    stats->cycles=kwt_icb32_cycles()-start;
    if(rc)return rc;
    if(!fault_seen || trap_count!=prior+1u || stats->first_error!=3u ||
       stats->error_addr!=KWT_ICB32_BASE+K16_CONTROL || stats->error_phase!=2u ||
       stats->source_acks || stats->stage_acks || stats->load_acks || stats->output_acks ||
       stats->load_committed || stats->output_committed || (stats->status&8u))return K16_DEVICE_ERROR;
    return K16_OK;
}

int main(void) {
    volatile uint32_t *mail=(volatile uint32_t *)(uintptr_t)0xa001f000u;
    const volatile uint32_t *meta=(const volatile uint32_t *)(uintptr_t)0x8000fff0u;
    uint32_t a=meta[1],b=meta[2],short_timeout=meta[3],phase=0,completed=0;
    int result=K16_OK;
    struct kwt_icb32_stats stats;
    mail[0]=0;mail[32]=0;mail[34]=0;
    if(meta[0]!=SEQUENCE_MAGIC || (a&31u)!=10u || (b&31u)!=10u || (a&0xffe0u) || (b&0xffe0u) ||
       ((a>>16)&1u)!=0 || ((b>>16)&1u)!=1 || (a>>17)<8u || (a>>17)>11752u || (b>>17)<8u || (b>>17)>11752u || short_timeout<4096u || short_timeout>32768u) {
        result=K16_BAD_ARGUMENT;goto finished;
    }
    for(phase=1;phase<=10;phase++) {
        uint32_t descriptor=phase==9 ? b : a,kind=phase<=5 ? 1u : phase==6 ? 2u : phase==7 ? 3u : 4u;
        uint32_t off=0,value=0,pre_source=0,pre_stage=0,pre_status=0;
        clear_stats(&stats);
        result=prepare_idle(&stats);
        if(result)goto finished;
        clear_stats(&stats);
        result=phase_begin(phase,descriptor);
        if(result)goto finished;
        configure(descriptor);
        if(phase<=5) {
            if(phase==1){off=K16_SOURCE_BASE;value=KWT_ICB32_SOURCE+2u;}
            if(phase==2){off=K16_INPUT_BASE;value=0xa007f000u;}
            if(phase==3){off=K16_OUTPUT_BASE;value=KWT_ICB32_INPUT;}
            if(phase==4){off=K16_INPUT_BYTES;value=28u;}
            if(phase==5){off=K16_OUTPUT_BYTES;value=KWT_ICB32_OUTPUT_BYTES-4u;}
            result=rejected_configuration(off,value,&stats);
            stats.primary_result=result;
        } else if(phase==6) {
            uint64_t start=kwt_icb32_cycles();
            write_reg(K16_CONTROL,1);fence_io();
            for(;;) {
                pre_source=read_reg(K16_SOURCE_ACKS);
                pre_stage=read_reg(K16_STAGE_ACKS);pre_status=read_reg(K16_STATUS);
                if((pre_status&16u) || kwt_icb32_cycles()-start>=KWT_SEQUENCE_CANCEL_TIMEOUT_CYCLES) {
                    result=K16_DEVICE_ERROR;break;
                }
                if(pre_source>=32u)break;
            }
            int cancelled=kwt_icb32_cancel(KWT_SEQUENCE_CANCEL_TIMEOUT_CYCLES,&stats);
            stats.cycles=kwt_icb32_cycles()-start;
            if(cancelled)result=cancelled;
            if(!result && (!(pre_status&1u) || pre_source>=(descriptor>>17) || pre_stage>=(descriptor>>17) ||
               stats.source_acks<pre_source || stats.source_acks>=(descriptor>>17) || stats.stage_acks>=(descriptor>>17) ||
               stats.load_acks>stats.stage_acks || stats.input_words>=23488u || stats.output_acks || stats.output_words || stats.output_committed ||
               stats.first_error || !stats.cancel_drained || (stats.status&8u)))result=K16_DEVICE_ERROR;
            stats.primary_result=result;
        } else {
            struct kwt_icb32_config cfg;
            cfg.source=KWT_ICB32_SOURCE;cfg.input=KWT_ICB32_INPUT;cfg.output=KWT_ICB32_OUTPUT;
            cfg.encoded_bytes=(descriptor>>17)*4u;cfg.shift=descriptor&31u;cfg.dma_mode=1;cfg.prefetch=1;cfg.layout=KWT_ICB32_LAYOUT;
            result=kwt_icb32_run(&cfg,phase==7 ? short_timeout : KWT_SEQUENCE_TIMEOUT_CYCLES,
                                 KWT_SEQUENCE_CANCEL_TIMEOUT_CYCLES,&stats);
            if(phase==7) {
                if(result!=K16_TIMEOUT || stats.primary_result!=K16_TIMEOUT || !stats.cancel_drained ||
                   !stats.source_acks || stats.source_acks>=(descriptor>>17) || stats.stage_acks>=(descriptor>>17) ||
                   stats.output_acks>=12672u || stats.output_words>=25344u ||
                   stats.output_committed!=stats.output_acks*4u || stats.first_error ||
                   (stats.status&8u) || !ready_and_drained()) {
                    if(result==K16_TIMEOUT || result==K16_OK)result=K16_DEVICE_ERROR;
                }
            }
        }
        receipt(phase,kind,result,descriptor,off,value,short_timeout,pre_source,pre_stage,pre_status,&stats);
        if(phase==7 && result==K16_TIMEOUT)result=K16_OK;
        if(result)goto finished;
        completed++;
    }
    phase=10;
    if(trap_count!=5u)result=K16_DEVICE_ERROR;
finished:
    mail[1]=(uint32_t)result;mail[2]=completed;mail[3]=phase;mail[4]=trap_count;
    mail[5]=SEQUENCE_MAGIC;mail[6]=0;mail[7]=a;mail[8]=b;mail[9]=short_timeout;
    fence_io();mail[0]=result ? 0xbad00032u : SEQUENCE_PASS;
    for(;;)__asm__ volatile("nop");
}
