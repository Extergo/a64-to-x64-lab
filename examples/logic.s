.text
.global logic
logic:
    movz x0, #65535, lsl #48
    movz x1, #7
    sub x2, x1, x0
    eor x3, x2, x1
    orr x4, x3, x0
    and x0, x4, x2
    add x30, x0, xzr
    add xzr, x30, x1
    nop
    ret
