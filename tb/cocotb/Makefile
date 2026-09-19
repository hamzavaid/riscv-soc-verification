TOPLEVEL_LANG := verilog
TOPLEVEL := rv32i_core
MODULE := test_m1_smoke

VERILOG_SOURCES := $(RTL_DIR)/rv32i_core.sv
SIM_BUILD := $(BUILD_DIR)
COCOTB_RESULTS_FILE := $(ARTIFACT_DIR)/results.xml
export PROGRAM_DIR
export PYTHONDONTWRITEBYTECODE := 1

ifeq ($(SIM),icarus)
COMPILE_ARGS += -g2012
endif

$(shell mkdir -p $(BUILD_DIR) $(ARTIFACT_DIR))

include $(shell $(COCOTB_CONFIG) --makefiles)/Makefile.sim
