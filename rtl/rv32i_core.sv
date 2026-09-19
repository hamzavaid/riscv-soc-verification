module rv32i_core (
    input  logic        clk,
    input  logic        rst_n,

    output logic        imem_req_o,
    output logic [31:0] imem_addr_o,
    input  logic [31:0] imem_rdata_i,
    input  logic        imem_valid_i,

    output logic        retire_valid_o,
    output logic [31:0] retire_pc_o,
    output logic [31:0] retire_insn_o,
    output logic        retire_rd_we_o,
    output logic [4:0]  retire_rd_o,
    output logic [31:0] retire_rd_data_o,

    output logic [31:0] debug_reg_x1_o
);

    typedef enum logic {
        FETCH,
        HALT
    } state_t;

    state_t state_q;
    logic [31:0] pc_q;
    logic [31:0] registers [0:31];
    integer register_index;

    logic [4:0] source_register;
    logic [4:0] destination_register;
    logic [31:0] immediate;
    logic [31:0] addi_result;
    logic is_addi;

    assign source_register = imem_rdata_i[19:15];
    assign destination_register = imem_rdata_i[11:7];
    assign immediate = {{20{imem_rdata_i[31]}}, imem_rdata_i[31:20]};
    assign addi_result = registers[source_register] + immediate;
    assign is_addi = (imem_rdata_i[6:0] == 7'b0010011)
                     && (imem_rdata_i[14:12] == 3'b000);

    assign imem_req_o = rst_n && (state_q == FETCH);
    assign imem_addr_o = pc_q;
    assign debug_reg_x1_o = registers[1];

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state_q <= FETCH;
            pc_q <= 32'h0000_0000;
            retire_valid_o <= 1'b0;
            retire_pc_o <= 32'h0000_0000;
            retire_insn_o <= 32'h0000_0000;
            retire_rd_we_o <= 1'b0;
            retire_rd_o <= 5'd0;
            retire_rd_data_o <= 32'h0000_0000;
            for (register_index = 0; register_index < 32; register_index = register_index + 1) begin
                registers[register_index] <= 32'h0000_0000;
            end
        end else begin
            retire_valid_o <= 1'b0;
            registers[0] <= 32'h0000_0000;

            if ((state_q == FETCH) && imem_valid_i) begin
                state_q <= HALT;

                if (is_addi) begin
                    retire_valid_o <= 1'b1;
                    retire_pc_o <= pc_q;
                    retire_insn_o <= imem_rdata_i;
                    retire_rd_we_o <= (destination_register != 5'd0);
                    retire_rd_o <= destination_register;
                    retire_rd_data_o <= addi_result;
                    pc_q <= pc_q + 32'd4;

                    if (destination_register != 5'd0) begin
                        registers[destination_register] <= addi_result;
                    end
                end
            end
        end
    end

endmodule
