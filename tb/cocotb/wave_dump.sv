`ifndef WAVE_FILE
`define WAVE_FILE "rv32i_core.vcd"
`endif

module cocotb_wave_dump;
    initial begin
        $dumpfile(`WAVE_FILE);
        $dumpvars(0, rv32i_core);
    end
endmodule
