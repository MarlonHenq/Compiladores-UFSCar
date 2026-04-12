# =============================================================================
# Makefile — Analisador Sintático da Linguagem LA (T2)
# =============================================================================
# Trabalho 2 – Construção de Compiladores – UFSCar (DC)
# Alunos: Marlon Henrique Sanches (RA819464) | Samuel Gerga Martins (RA821772)
#
# Targets principais:
#   make generate  — gera o lexer e parser a partir de LA.g4 (ANTLR4)
#   make run       — executa o analisador sintático (requer INPUT e OUTPUT)
#   make test      — roda os 62 casos de teste e compara com saídas esperadas
#   make clean     — remove arquivos gerados
#   make help      — mostra instruções de uso
# =============================================================================

PY          = python3
ANTLR       = antlr4
GRAMMAR     = LA.g4
TEST_DIR    = 2.casos_teste_t2
ENTRADA_DIR = $(TEST_DIR)/entrada
SAIDA_DIR   = $(TEST_DIR)/saida
BUILD_DIR   = build

# Lista todos os arquivos de entrada dos casos de teste
ENTRADAS = $(wildcard $(ENTRADA_DIR)/*.txt)

.PHONY: help generate run test clean

# Target padrão: mostra instruções de uso
help:
	@echo "=== Analisador Sintático LA (T2) ==="
	@echo ""
	@echo "Uso:"
	@echo "  make generate                              # Gera lexer/parser via ANTLR4"
	@echo "  make run INPUT=entrada.txt OUTPUT=saida.txt # Executa o analisador"
	@echo "  make test                                  # Roda os 62 casos de teste"
	@echo "  make clean                                 # Remove arquivos gerados"
	@echo ""
	@echo "Pré-requisitos:"
	@echo "  - Python 3.10+"
	@echo "  - antlr4-tools (comando 'antlr4')"
	@echo "  - antlr4-python3-runtime (pip install antlr4-python3-runtime)"

# Gera os arquivos do lexer e parser a partir da gramática LA.g4
# Saída: LALexer.py, LAParser.py, LAListener.py, LA.tokens, etc.
generate: $(GRAMMAR)
	$(ANTLR) -Dlanguage=Python3 $(GRAMMAR)
	@echo "[OK] Lexer e Parser gerados com sucesso."

# Executa o analisador sintático com os caminhos de entrada e saída fornecidos
run:
	@if [ -z "$(INPUT)" ] || [ -z "$(OUTPUT)" ]; then \
		echo "Uso: make run INPUT=arquivo_entrada OUTPUT=arquivo_saida"; exit 1; \
	fi
	$(PY) main.py "$(INPUT)" "$(OUTPUT)"

# Roda todos os 62 casos de teste e compara as saídas geradas com as esperadas
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

# Remove arquivos gerados pelo ANTLR4 e saídas de teste
clean:
	rm -f LALexer.py LAParser.py LAListener.py LAVisitor.py
	rm -f LA.tokens LALexer.tokens LA.interp LALexer.interp
	rm -f LALexer.interp LAParser.interp
	rm -rf __pycache__
	rm -rf "$(BUILD_DIR)"
	@echo "[OK] Arquivos gerados removidos."
