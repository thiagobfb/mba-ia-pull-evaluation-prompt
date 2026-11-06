"""
Roda o prompt v2 LOCAL contra os relatos de tests/cenarios_avaliacao.yml.

Faz uma chamada real ao LLM do .env por cenário, sem usar o Hub nem criar experimento.
Serve para ver as respostas antes do push. A nota oficial vem de src/evaluate.py.

Uso:
    python tests/testar_cenarios.py
    python tests/testar_cenarios.py --cenario complexo
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from push_prompts import PROMPT_NAME, PROMPT_PATH, build_prompt_template
from utils import check_env_vars, get_llm, load_yaml, print_section_header

CENARIOS_PATH = Path(__file__).parent / "cenarios_avaliacao.yml"


def conferir(resposta: str, cenario: dict) -> list:
    """Devolve a lista de problemas encontrados na resposta."""
    texto = resposta.lower()
    faltando = [t for t in cenario["deve_conter"] if t.lower() not in texto]
    proibidos = [t for t in cenario["nao_deve_conter"] if t.lower() in texto]
    return [f'faltou "{t}"' for t in faltando] + [f'não deveria conter "{t}"' for t in proibidos]


def main():
    parser = argparse.ArgumentParser(description="Testa o prompt v2 local nos cenários da avaliação")
    parser.add_argument("--cenario", help="id de um único cenário")
    args = parser.parse_args()

    if not check_env_vars(["LLM_PROVIDER", "LLM_MODEL"]):
        return 1

    cenarios = load_yaml(str(CENARIOS_PATH))["cenarios"]
    if args.cenario:
        cenarios = [c for c in cenarios if c["id"] == args.cenario]
        if not cenarios:
            print(f"❌ Cenário não encontrado: {args.cenario}")
            return 1

    chain = build_prompt_template(load_yaml(str(PROMPT_PATH))[PROMPT_NAME]) | get_llm(temperature=0)

    reprovados = []
    for cenario in cenarios:
        print_section_header(f"{cenario['id']}: {cenario['objetivo']}")
        try:
            resposta = chain.invoke({"bug_report": cenario["relato"]}).text
        except Exception as e:
            print(f"❌ Falha ao chamar o LLM: {e}")
            reprovados.append(cenario["id"])
            continue

        print(resposta)
        problemas = conferir(resposta, cenario)
        print()
        if problemas:
            reprovados.append(cenario["id"])
            for problema in problemas:
                print(f"❌ {problema}")
        else:
            print("✓ Forma da resposta conferida")

    print_section_header("RESUMO")
    print(f"Aprovados: {len(cenarios) - len(reprovados)} de {len(cenarios)}")
    if reprovados:
        print(f"Reprovados: {', '.join(reprovados)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
