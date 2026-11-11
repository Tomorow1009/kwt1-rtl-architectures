.section .text.start,"ax",@progbits
.globl _start
_start:
    .option push
    .option norelax
    la gp, __global_pointer$
    .option pop
    la sp, __stack_top
    csrw mie, zero
    csrw mstatus, zero
    la t0, trap_entry
    csrw mtvec, t0
    la t0, __bss_start
    la t1, __bss_end
1:  bgeu t0,t1,2f
    sw zero,0(t0)
    addi t0,t0,4
    j 1b
2:  call main
3:  j 3b
.balign 4
trap_entry:
    li t0,0xa001f000
    csrr t1,mcause
    sw t1,4(t0)
    csrr t1,mepc
    sw t1,8(t0)
    csrr t1,mtval
    sw t1,12(t0)
    li t1,0xbad00001
    sw t1,0(t0)
4:  j 4b
