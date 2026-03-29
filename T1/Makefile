PY=python3
TEST_DIR=casos_de_teste
BUILD_DIR=build
ENTRADAS=$(wildcard $(TEST_DIR)/entrada*)

# Suporte a chamada posicional `make <entrada> <saida>`
# Ex.: `make $(TEST_DIR)/entrada1 saida`
ARGS=$(filter-out run test clean help,$(MAKECMDGOALS))

# Quando exatamente dois argumentos são passados, executa o lexer diretamente
ifeq ($(words $(ARGS)),2)
.PHONY: $(firstword $(ARGS)) $(word 2,$(ARGS))
$(firstword $(ARGS)) $(word 2,$(ARGS)):
	@in_file=$(word 1,$(ARGS)); out_file=$(word 2,$(ARGS)); \
	$(PY) main.py "$$in_file" "$$out_file"
endif

.PHONY: help run run-positional test clean

help:
	@echo "Uso:";
	@echo "  make <arquivo_entrada> <arquivo_saida>   # executa lexer";
	@echo "  make run INPUT=arq_entrada OUTPUT=arq_saida";
	@echo "  make test                                # roda casos em $(TEST_DIR)/";
	@echo "  make clean                               # remove build/";

run:
	@if [ -z "$(INPUT)" ] || [ -z "$(OUTPUT)" ]; then \
		echo "Uso: make run INPUT=arquivo_de_entrada OUTPUT=arquivo_de_saida"; exit 1; \
	fi
	$(PY) main.py "$(INPUT)" "$(OUTPUT)"

# Executa todos os casos de teste presentes em casos_de_teste/ e compara com as saídas esperadas
# Saídas geradas vão para build/saidaX

test:
	@mkdir -p "$(BUILD_DIR)"
	@status=0; \
	for in_file in $(ENTRADAS); do \
		base=$$(basename $$in_file); \
		num=$${base#entrada}; \
		out_file="$(BUILD_DIR)/saida$${num}"; \
		exp_file="$(TEST_DIR)/saida$${num}"; \
		echo "[TEST] $$in_file -> $$out_file"; \
		$(PY) main.py "$$in_file" "$$out_file"; \
		if ! diff -u "$$exp_file" "$$out_file"; then \
			echo "  Falhou: $$in_file"; status=1; \
		else \
			echo "  OK"; \
		fi; \
	done; \
	if [ $$status -ne 0 ]; then \
		echo "Alguns testes falharam."; exit $$status; \
	else \
		echo "Todos os testes passaram."; \
	fi

clean:
	@rm -rf "$(BUILD_DIR)"

# Evita que make tente criar arquivos com os nomes dos argumentos posicionais
%::
	@:
