module rv32i_core (
    input  logic        clk,
    input  logic        rst_n,

    output logic        imem_req_o,
    output logic [31:0] imem_addr_o,
    input  logic [31:0] imem_rdata_i,
    input  logic        imem_valid_i,

    output logic        dmem_req_o,
    output logic        dmem_we_o,
    output logic [31:0] dmem_addr_o,
    output logic [31:0] dmem_wdata_o,
    output logic [3:0]  dmem_wstrb_o,
    input  logic [31:0] dmem_rdata_i,
    input  logic        dmem_valid_i,

    output logic        retire_valid_o,
    output logic [31:0] retire_pc_o,
    output logic [31:0] retire_insn_o,
    output logic        retire_rd_we_o,
    output logic [4:0]  retire_rd_o,
    output logic [31:0] retire_rd_data_o,
    output logic        retire_mem_valid_o,
    output logic        retire_mem_we_o,
    output logic [31:0] retire_mem_addr_o,
    output logic [31:0] retire_mem_wdata_o,
    output logic        retire_trap_o,

    output logic [31:0] debug_reg_x1_o
);

    typedef enum logic [1:0] {
        FETCH,
        MEMORY,
        HALT
    } state_t;

    state_t state_q;
    logic [31:0] pc_q;
    logic [31:0] registers [0:31];
    integer register_index;

    logic [31:0] pending_pc_q;
    logic [31:0] pending_insn_q;
    logic [4:0]  pending_rd_q;
    logic [31:0] pending_address_q;
    logic [31:0] pending_write_data_q;
    logic        pending_load_q;

    logic [6:0] opcode;
    logic [4:0] source_register_1;
    logic [4:0] source_register_2;
    logic [4:0] destination_register;
    logic [2:0] funct3;
    logic [6:0] funct7;
    logic [31:0] immediate_i;
    logic [31:0] immediate_s;
    logic [31:0] immediate_b;
    logic [31:0] immediate_j;

    logic decoded_supported;
    logic decoded_memory;
    logic decoded_load;
    logic decoded_rd_write;
    logic [31:0] decoded_result;
    logic [31:0] decoded_next_pc;
    logic [31:0] decoded_memory_address;
    logic [31:0] decoded_memory_write_data;

    assign opcode = imem_rdata_i[6:0];
    assign destination_register = imem_rdata_i[11:7];
    assign funct3 = imem_rdata_i[14:12];
    assign source_register_1 = imem_rdata_i[19:15];
    assign source_register_2 = imem_rdata_i[24:20];
    assign funct7 = imem_rdata_i[31:25];
    assign immediate_i = {{20{imem_rdata_i[31]}}, imem_rdata_i[31:20]};
    assign immediate_s = {
        {20{imem_rdata_i[31]}}, imem_rdata_i[31:25], imem_rdata_i[11:7]
    };
    assign immediate_b = {
        {19{imem_rdata_i[31]}},
        imem_rdata_i[31],
        imem_rdata_i[7],
        imem_rdata_i[30:25],
        imem_rdata_i[11:8],
        1'b0
    };
    assign immediate_j = {
        {11{imem_rdata_i[31]}},
        imem_rdata_i[31],
        imem_rdata_i[19:12],
        imem_rdata_i[20],
        imem_rdata_i[30:21],
        1'b0
    };

    assign imem_req_o = rst_n && (state_q == FETCH);
    assign imem_addr_o = pc_q;
    assign dmem_req_o = rst_n && (state_q == MEMORY);
    assign dmem_we_o = dmem_req_o && !pending_load_q;
    assign dmem_addr_o = pending_address_q;
    assign dmem_wdata_o = pending_write_data_q;
    assign dmem_wstrb_o = dmem_we_o ? 4'hf : 4'h0;
    assign debug_reg_x1_o = registers[1];

    always_comb begin
        decoded_supported = 1'b1;
        decoded_memory = 1'b0;
        decoded_load = 1'b0;
        decoded_rd_write = 1'b0;
        decoded_result = 32'h0000_0000;
        decoded_next_pc = pc_q + 32'd4;
        decoded_memory_address = 32'h0000_0000;
        decoded_memory_write_data = 32'h0000_0000;

        case (opcode)
            7'h13: begin
                decoded_rd_write = (destination_register != 5'd0);
                case (funct3)
                    3'h0: decoded_result = registers[source_register_1] + immediate_i;
                    3'h4: decoded_result = registers[source_register_1] ^ immediate_i;
                    3'h6: decoded_result = registers[source_register_1] | immediate_i;
                    3'h7: decoded_result = registers[source_register_1] & immediate_i;
                    default: decoded_supported = 1'b0;
                endcase
            end
            7'h33: begin
                decoded_rd_write = (destination_register != 5'd0);
                case ({funct7, funct3})
                    {7'h00, 3'h0}: decoded_result =
                        registers[source_register_1] + registers[source_register_2];
                    {7'h20, 3'h0}: decoded_result =
                        registers[source_register_1] - registers[source_register_2];
                    {7'h00, 3'h4}: decoded_result =
                        registers[source_register_1] ^ registers[source_register_2];
                    {7'h00, 3'h6}: decoded_result =
                        registers[source_register_1] | registers[source_register_2];
                    {7'h00, 3'h7}: decoded_result =
                        registers[source_register_1] & registers[source_register_2];
                    default: decoded_supported = 1'b0;
                endcase
            end
            7'h03: begin
                if (funct3 == 3'h2) begin
                    decoded_memory = 1'b1;
                    decoded_load = 1'b1;
                    decoded_rd_write = (destination_register != 5'd0);
                    decoded_memory_address = registers[source_register_1] + immediate_i;
                end else begin
                    decoded_supported = 1'b0;
                end
            end
            7'h23: begin
                if (funct3 == 3'h2) begin
                    decoded_memory = 1'b1;
                    decoded_memory_address = registers[source_register_1] + immediate_s;
                    decoded_memory_write_data = registers[source_register_2];
                end else begin
                    decoded_supported = 1'b0;
                end
            end
            7'h63: begin
                case (funct3)
                    3'h0: begin
                        if (registers[source_register_1] == registers[source_register_2]) begin
                            decoded_next_pc = pc_q + immediate_b;
                        end
                    end
                    3'h1: begin
                        if (registers[source_register_1] != registers[source_register_2]) begin
                            decoded_next_pc = pc_q + immediate_b;
                        end
                    end
                    default: decoded_supported = 1'b0;
                endcase
            end
            7'h6f: begin
                decoded_rd_write = (destination_register != 5'd0);
                decoded_result = pc_q + 32'd4;
                decoded_next_pc = pc_q + immediate_j;
            end
            7'h67: begin
                if (funct3 == 3'h0) begin
                    decoded_rd_write = (destination_register != 5'd0);
                    decoded_result = pc_q + 32'd4;
                    decoded_next_pc = (registers[source_register_1] + immediate_i)
                                      & 32'hffff_fffe;
                end else begin
                    decoded_supported = 1'b0;
                end
            end
            default: decoded_supported = 1'b0;
        endcase
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state_q <= FETCH;
            pc_q <= 32'h0000_0000;
            pending_pc_q <= 32'h0000_0000;
            pending_insn_q <= 32'h0000_0000;
            pending_rd_q <= 5'd0;
            pending_address_q <= 32'h0000_0000;
            pending_write_data_q <= 32'h0000_0000;
            pending_load_q <= 1'b0;
            retire_valid_o <= 1'b0;
            retire_pc_o <= 32'h0000_0000;
            retire_insn_o <= 32'h0000_0000;
            retire_rd_we_o <= 1'b0;
            retire_rd_o <= 5'd0;
            retire_rd_data_o <= 32'h0000_0000;
            retire_mem_valid_o <= 1'b0;
            retire_mem_we_o <= 1'b0;
            retire_mem_addr_o <= 32'h0000_0000;
            retire_mem_wdata_o <= 32'h0000_0000;
            retire_trap_o <= 1'b0;
            for (register_index = 0; register_index < 32; register_index = register_index + 1) begin
                registers[register_index] <= 32'h0000_0000;
            end
        end else begin
            retire_valid_o <= 1'b0;
            retire_rd_we_o <= 1'b0;
            retire_rd_o <= 5'd0;
            retire_rd_data_o <= 32'h0000_0000;
            retire_mem_valid_o <= 1'b0;
            retire_mem_we_o <= 1'b0;
            retire_mem_addr_o <= 32'h0000_0000;
            retire_mem_wdata_o <= 32'h0000_0000;
            retire_trap_o <= 1'b0;
            registers[0] <= 32'h0000_0000;

            if ((state_q == FETCH) && imem_valid_i) begin
                if (!decoded_supported) begin
                    retire_valid_o <= 1'b1;
                    retire_pc_o <= pc_q;
                    retire_insn_o <= imem_rdata_i;
                    retire_trap_o <= 1'b1;
                    state_q <= HALT;
                end else if (decoded_memory) begin
                    pending_pc_q <= pc_q;
                    pending_insn_q <= imem_rdata_i;
                    pending_rd_q <= decoded_rd_write ? destination_register : 5'd0;
                    pending_address_q <= decoded_memory_address;
                    pending_write_data_q <= decoded_memory_write_data;
                    pending_load_q <= decoded_load;
                    state_q <= MEMORY;
                end else begin
                    retire_valid_o <= 1'b1;
                    retire_pc_o <= pc_q;
                    retire_insn_o <= imem_rdata_i;
                    retire_rd_we_o <= decoded_rd_write;
                    retire_rd_o <= decoded_rd_write ? destination_register : 5'd0;
                    retire_rd_data_o <= decoded_rd_write ? decoded_result : 32'h0000_0000;
                    pc_q <= decoded_next_pc;
                    if (decoded_rd_write) begin
                        registers[destination_register] <= decoded_result;
                    end
                end
            end else if ((state_q == MEMORY) && dmem_valid_i) begin
                retire_valid_o <= 1'b1;
                retire_pc_o <= pending_pc_q;
                retire_insn_o <= pending_insn_q;
                retire_rd_we_o <= pending_load_q && (pending_rd_q != 5'd0);
                retire_rd_o <= pending_load_q ? pending_rd_q : 5'd0;
                retire_rd_data_o <= pending_load_q ? dmem_rdata_i : 32'h0000_0000;
                retire_mem_valid_o <= 1'b1;
                retire_mem_we_o <= !pending_load_q;
                retire_mem_addr_o <= pending_address_q;
                retire_mem_wdata_o <= pending_load_q
                    ? 32'h0000_0000 : pending_write_data_q;
                pc_q <= pending_pc_q + 32'd4;
                state_q <= FETCH;
                if (pending_load_q && (pending_rd_q != 5'd0)) begin
                    registers[pending_rd_q] <= dmem_rdata_i;
                end
            end
        end
    end

endmodule
