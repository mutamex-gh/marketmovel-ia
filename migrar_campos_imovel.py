"""
Script de migração — Adiciona campos completos de imóvel ao banco SQLite existente.
Executa ALTER TABLE ADD COLUMN para cada novo campo.
Seguro para rodar múltiplas vezes (verifica se a coluna já existe).
"""
import sqlite3
import sys

DB_PATH = "marketplace.db"

NOVAS_COLUNAS = [
    ("banheiros",       "INTEGER"),
    ("suites",          "INTEGER"),
    ("vagas_garagem",   "INTEGER"),
    ("area_construida", "REAL"),
    ("andar",           "INTEGER"),
    ("aceita_pets",     "INTEGER DEFAULT 0"),      # Boolean → 0/1 no SQLite
    ("mobiliado",       "VARCHAR(20) DEFAULT 'nao'"),
    ("condominio",      "REAL"),
    ("iptu",            "REAL"),
    ("finalidade",      "VARCHAR(20) DEFAULT 'venda'"),
]


def coluna_existe(cursor, tabela: str, coluna: str) -> bool:
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas = [row[1] for row in cursor.fetchall()]
    return coluna in colunas


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    adicionadas = 0
    ja_existiam = 0

    for nome, tipo in NOVAS_COLUNAS:
        if coluna_existe(cursor, "imoveis", nome):
            print(f"  ✓ Coluna '{nome}' já existe — pulando.")
            ja_existiam += 1
        else:
            sql = f"ALTER TABLE imoveis ADD COLUMN {nome} {tipo}"
            cursor.execute(sql)
            print(f"  + Coluna '{nome}' adicionada com sucesso.")
            adicionadas += 1

    conn.commit()
    conn.close()

    print(f"\nMigração finalizada: {adicionadas} colunas adicionadas, {ja_existiam} já existiam.")


if __name__ == "__main__":
    main()
