OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY {
  ITCM (rx) : ORIGIN = 0x80000000, LENGTH = 0x0000fff0
  DTCM (rw) : ORIGIN = 0x90000000, LENGTH = 0x00040000
}
SECTIONS {
  .text : { KEEP(*(.text.start)) *(.text .text.*) *(.rodata .rodata.*) } > ITCM
  .data : { *(.data .data.* .sdata .sdata.*) } > DTCM
  .bss (NOLOAD) : { . = ALIGN(4); __bss_start = .; *(.bss .bss.* .sbss .sbss.* COMMON) . = ALIGN(4); __bss_end = .; } > DTCM
  __global_pointer$ = ORIGIN(DTCM) + 0x800;
  __stack_top = ORIGIN(DTCM) + LENGTH(DTCM) - 16;
  ASSERT(SIZEOF(.data) == 0, "Startup does not copy initialized DTCM data")
  ASSERT(__bss_end < __stack_top - 0x4000, "DTCM stack overlap")
  /DISCARD/ : { *(.comment) *(.eh_frame*) }
}
