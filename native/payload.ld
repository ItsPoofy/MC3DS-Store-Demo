SECTIONS {
    . = 0x003E0478;
    .payload : {
        KEEP(*(.text.catalog_entry))
        *(.text*)
        *(.rodata*)
    }
    /DISCARD/ : { *(.comment) *(.ARM.attributes) *(.ARM.exidx*) *(.ARM.extab*) }
    ASSERT(SIZEOF(.payload) <= 0x9B0, "Offline catalog exceeds replaced function")
    ASSERT(SIZEOF(.data) == 0, "Payload must not have writable data")
    ASSERT(SIZEOF(.bss) == 0, "Payload must not have writable data")
}
