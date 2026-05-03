# Makefile — Analisador semântico LA (T3)
# Targets: generate, run, test, clean, help

PY          = python3
ANTLR       = antlr4
GRAMMAR     = LA.g4
TEST_DIR    = 3.casos_teste_t3
ENTRADA_DIR = $(TEST_DIR)/entrada
SAIDA_DIR   = $(TEST_DIR)/saida
BUILD_DIR   = build

ENTRADAS = $(wildcard $(ENTRADA_DIR)/*.txt)

.PHONY: help generate run test clean

help:
	@echo "=== Analisador Semântico LA (T3) ==="
	@echo "  (opcional se antlr4-tools não baixar o JAR:) export ANTLR4_TOOLS_ANTLR_VERSION=4.13.2"
	@echo "  make generate                              # antlr4 -visitor LA.g4"
	@echo "  make run INPUT=... OUTPUT=... "
	@echo "  make test"
	@echo "  make clean"

generate: $(GRAMMAR)
	$(ANTLR) -Dlanguage=Python3 -visitor $(GRAMMAR)
	@echo "[OK] LAVisitor.py e demais artefatos gerados."

run:
	@if [ -z "$(INPUT)" ] || [ -z "$(OUTPUT)" ]; then \
		echo "Uso: make run INPUT=arquivo_entrada OUTPUT=arquivo_saida"; exit 1; \
	fi
	$(PY) main.py "$(INPUT)" "$(OUTPUT)"

test:
	@mkdir -p "$(BUILD_DIR)"
	@total=0; passou=0; falhou=0; \
	for entrada in $(ENTRADAS); do \
		base=$$(basename "$$entrada"); \
		saida_gerada="$(BUILD_DIR)/$$base"; \
		saida_esperada="$(SAIDA_DIR)/$$base"; \
		total=$$((total + 1)); \
		$(PY) main.py "$$entrada" "$$saida_gerada" 2>/dev/null; \
		if [ ! -f "$$saida_esperada" ]; then \
			echo "[SKIP] $$base"; \
		elif diff -q "$$saida_esperada" "$$saida_gerada" > /dev/null 2>&1; then \
			echo "[OK]   $$base"; \
			passou=$$((passou + 1)); \
		else \
			echo "[FAIL] $$base"; \
			diff -u "$$saida_esperada" "$$saida_gerada" 2>/dev/null || true; \
			falhou=$$((falhou + 1)); \
		fi; \
	done; \
	echo ""; \
	echo "=== $$passou/$$total OK, $$falhou falharam ==="; \
	if [ $$falhou -ne 0 ]; then exit 1; fi

clean:
	rm -f LALexer.py LAParser.py LAListener.py LAVisitor.py
	rm -f LA.tokens LALexer.tokens LA.interp LALexer.interp LAParser.interp
	rm -rf __pycache__
	rm -rf "$(BUILD_DIR)"
	@echo "[OK] Limpo."
