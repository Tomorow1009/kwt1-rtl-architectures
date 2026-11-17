#ifndef KWT_G32_H
#define KWT_G32_H
#include <stdint.h>

#define KWT_ICB32_BASE 0x40000000u
#ifndef KWT_ICB32_ROWS
#define KWT_ICB32_ROWS 2u
#endif
#if KWT_ICB32_ROWS != 2
#error "G32-A requires exactly two rows"
#endif
#define KWT_ICB32_ID_VALUE 0x4b57530fu
#define KWT_ICB32_SOURCE 0xb0000000u
#define KWT_ICB32_INPUT 0xa0000000u
#define KWT_ICB32_OUTPUT 0xa000c000u
#define KWT_ICB32_SHARED_BYTES 0x80000u
#define KWT_ICB32_MAX_INPUT_BYTES 46496u
#define KWT_ICB32_OUTPUT_BYTES 50688u
#define KWT_ICB32_LAYOUT 0x00100006u
#define KWT_G32_NUMERIC_FORMAT 0x000e0c20u
#define KWT_G32_CAPABILITY 0x000d02bfu
#ifndef KWT_G32_TRANSACTION_DEPTH
#define KWT_G32_TRANSACTION_DEPTH 2u
#endif
#if KWT_G32_TRANSACTION_DEPTH != 2
#error "G32 metadata depth must be 2"
#endif
#define KWT_ICB32_INPUT_HALVES 23488u
#define KWT_ICB32_OUTPUT_HALVES 25344u
#ifndef KWT_ICB32_USE_IRQ
#define KWT_ICB32_USE_IRQ 0
#endif
/* GPIOB io_devices_0_15 maps to ID16 (bit0 is reserved in the fixed PLIC).
 * IRQ builds still require explicit verified register addresses below. */
#ifndef KWT_DMA_IRQ_ID
#define KWT_DMA_IRQ_ID 16u
#endif
#if KWT_ICB32_USE_IRQ
#if !defined(KWT_DMA_IRQ_MAPPING_VERIFIED) || KWT_DMA_IRQ_MAPPING_VERIFIED != 1
#error "IRQ firmware requires an explicitly verified PLIC/CLINT mapping"
#endif
#if !defined(KWT_PLIC_PRIORITY_ADDR) || !defined(KWT_PLIC_ENABLE_ADDR) || !defined(KWT_PLIC_ENABLE_MASK) || !defined(KWT_PLIC_THRESHOLD_ADDR) || !defined(KWT_PLIC_CLAIM_ADDR) || !defined(KWT_MTIME_ADDR) || !defined(KWT_MTIMECMP_ADDR) || !defined(KWT_TIMER_WAKE_TICKS) || !defined(KWT_TIMER_PROBE_CYCLES)
#error "Provide every PLIC/CLINT address and timer parameter explicitly"
#endif
#endif

enum kwt_icb32_reg {
    K16_ID=0x00, K16_CONTROL=0x04, K16_STATUS=0x08, K16_SHIFT=0x0c,
    K16_LOAD=0x10, K16_OUTPUT=0x14, K16_LOAD_COUNT=0x18, K16_OUTPUT_COUNT=0x1c,
    K16_FIRST_ERROR=0x20, K16_MODE=0x24, K16_SOURCE_BASE=0x28,
    K16_INPUT_BASE=0x2c, K16_OUTPUT_BASE=0x30, K16_INPUT_BYTES=0x34,
    K16_OUTPUT_BYTES=0x38, K16_LAYOUT=0x3c, K16_IRQ_ENABLE=0x40,
    K16_IRQ_STATUS=0x44, K16_FIRST_ERROR_ADDR=0x48, K16_FIRST_ERROR_PHASE=0x4c,
    K16_LOAD_COMMITTED=0x50, K16_OUTPUT_COMMITTED=0x54, K16_PENDING=0x58,
    K16_COMPLETION=0x5c, K16_SOURCE_ACKS=0x60, K16_STAGE_ACKS=0x64,
    K16_LOAD_ACKS=0x68, K16_OUTPUT_ACKS=0x6c, K16_SAT_COUNT=0x70,
    K16_CAPABILITY=0x74, K16_NUMERIC_FORMAT=0x8c,
    K16_TRANSACTION_DEPTH=0x90, K16_ACCEPTED_QUEUE=0x94, K16_ACCEPTED_CREDIT_STALLS=0x98
};
enum kwt_icb32_result {
    K16_OK=0, K16_TIMEOUT=-1, K16_DEVICE_ERROR=-2, K16_BAD_OUTPUT=-3,
    K16_BAD_ARGUMENT=-4, K16_NOT_DRAINED=-5, K16_BAD_ID=-6,
    K16_TIMER_NOT_VERIFIED=-7, K16_UNHANDLED_IRQ=-8
};
struct kwt_icb32_config {
    uint32_t source, input, output, shift, encoded_bytes;
    uint32_t dma_mode, prefetch, layout;
};
struct kwt_icb32_stats {
    uint64_t cycles;
    uint32_t input_words, output_words, saturated;
    uint32_t status, completion, pending, first_error, error_addr, error_phase;
    uint32_t load_committed, output_committed;
    uint32_t source_acks, stage_acks, load_acks, output_acks;
    uint32_t irq_events, external_irqs, timer_irqs, wfi_count, unhandled_irqs;
    uint32_t last_mcause, cancel_drained;
    int32_t primary_result;
};
uint64_t kwt_icb32_cycles(void);
void kwt_icb32_snapshot(struct kwt_icb32_stats *stats);
/* CANCEL preserves diagnostics and waits for valid requests/responses to drain.
 * A stuck slave returns NOT_DRAINED; it never reports cancellation complete. */
int kwt_icb32_cancel(uint64_t timeout_cycles, struct kwt_icb32_stats *stats);
/* This driver accepts DMA mode=1 and explicit encoded length. The separate
 * hardware MMIO debug interface remains available. No task inputs in ITCM. */
int kwt_icb32_run(const struct kwt_icb32_config *config, uint64_t timeout_cycles,
                 uint64_t cancel_timeout_cycles, struct kwt_icb32_stats *stats);
void kwt_icb32_trap(uint32_t mcause, uint32_t mepc, uint32_t mtval);
/* Optional board integration for the preserved GPIOB/shared PLIC source.
 * Return nonzero only after clearing the other peripheral's interrupt. */
int kwt_icb32_shared_irq_hook(uint32_t claim);
#endif
