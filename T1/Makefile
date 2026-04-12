# =============================================================================
# Makefile — Analisador Léxico da Linguagem LA (T1)
# =============================================================================
# Trabalho 1 – Construção de Compiladores – UFSCar (DC)
# Alunos: Marlon Henrique Sanches (RA819464) | Samuel Gerga Martins (RA821772)
#
# Targets principais:
#   make run       — executa o analisador léxico (requer INPUT e OUTPUT)
#   make test      — roda os 37 casos de teste e compara com saídas esperadas
#   make clean     — remove arquivos gerados
#   make help      — mostra instruções de uso
# =============================================================================

PY          = python3
TEST_DIR    = 1.casos_teste_t1
ENTRADA_DIR = $(TEST_DIR)/entrada
SAIDA_DIR   = $(TEST_DIR)/saida
BUILD_DIR   = build

# Lista todos os arquivos de entrada dos casos de teste
ENTRADAS = $(wildcard $(ENTRADA_DIR)/*.txt)

.PHONY: help run test clean

# Target padrão: mostra instruções de uso
help:
	@echo "=== Analisador Léxico LA (T1) ==="
	@echo ""
	@echo "Uso:"
	@echo "  make run INPUT=entrada.txt OUTPUT=saida.txt  # Executa o analisador"
	@echo "  make test                                    # Roda os 37 casos de teste"
	@echo "  make clean                                   # Remove arquivos gerados"

# Executa o analisador léxico com os caminhos de entrada e saída fornecidos
run:
	@if [ -z "$(INPUT)" ] || [ -z "$(OUTPUT)" ]; then \
		echo "Uso: make run INPUT=arquivo_entrada OUTPUT=arquivo_saida"; exit 1; \
	fi
	$(PY) main.py "$(INPUT)" "$(OUTPUT)"

# Roda todos os 37 casos de teste e compara as saídas geradas com as esperadas
# Saídas geradas ficam em build/ para não poluir o diretório de trabalho
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
			echo "[SKIP] $$base (saída esperada não encontrada)"; \
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
	echo "=== Resultado: $$passou/$$total passaram, $$falhou falharam ==="; \
	if [ $$falhou -ne 0 ]; then exit 1; fi

# Remove saídas de teste geradas
clean:
	rm -rf "$(BUILD_DIR)"
	rm -rf __pycache__
	@echo "[OK] Arquivos gerados removidos."
