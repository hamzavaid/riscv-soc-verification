TOPLEVEL_LANG := verilog
TOPLEVEL := rv32i_core
MODULE := test_m1_smoke

VERILOG_SOURCES := $(RTL_DIR)/rv32i_core.sv
SIM_BUILD := $(BUILD_DIR)
COCOTB_RESULTS_FILE := $(ARTIFACT_DIR)/results.xml
export PROGRAM_DIR
export PYTHONDONTWRITEBYTECODE := 1

# cocotb 1.9's Icarus WAVES mode forces FST. Keep it disabled and use TRACE
# below so Icarus emits VCD while Verilator emits FST.
override WAVES := 0

ifeq ($(SIM),icarus)
COMPILE_ARGS += -g2012
ifeq ($(TRACE),1)
VERILOG_SOURCES += $(CURDIR)/wave_dump.sv
COMPILE_ARGS += -s cocotb_wave_dump
COMPILE_ARGS += -DWAVE_FILE=\"$(ARTIFACT_DIR)/rv32i_core.vcd\"
endif
endif

ifeq ($(SIM),verilator)
ifeq ($(TRACE),1)
COMPILE_ARGS += --trace-fst --trace-structs
SIM_ARGS += --trace --trace-file $(ARTIFACT_DIR)/rv32i_core.fst
endif
endif

$(shell mkdir -p $(BUILD_DIR) $(ARTIFACT_DIR))

include $(shell $(COCOTB_CONFIG) --makefiles)/Makefile.sim
