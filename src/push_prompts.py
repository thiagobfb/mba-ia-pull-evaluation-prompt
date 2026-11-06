"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langsmith.utils import LangSmithConflictError, LangSmithUserError
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPT_NAME = "bug_to_user_story_v2"
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / f"{PROMPT_NAME}.yml"


def build_prompt_template(prompt_data: dict) -> ChatPromptTemplate:
    """Monta o template com as mensagens de sistema e de usuário."""
    return ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("user", prompt_data["user_prompt"]),
    ])


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    username = os.getenv("USERNAME_LANGSMITH_HUB")
    prompt_id = f"{username}/{prompt_name}"
    techniques = prompt_data["techniques_applied"]
    description = f"{prompt_data['description']}. Técnicas: {', '.join(techniques)}."
    tags = prompt_data["tags"] + [f"tecnica:{technique}" for technique in techniques]

    try:
        url = Client().push_prompt(
            prompt_id,
            object=build_prompt_template(prompt_data),
            is_public=True,
            description=description,
            tags=tags,
        )
    except LangSmithConflictError:
        print(f"ℹ️  {prompt_id} já está atualizado: não há nada novo para publicar.")
        return True
    except LangSmithUserError as e:
        print(f"❌ Não foi possível publicar {prompt_id}: {e}")
        print("\nSe você ainda não tem handle, crie-o pelo menu Make Public em um prompt.")
        print("Se já tem, confira USERNAME_LANGSMITH_HUB no .env.")
        return False
    except Exception as e:
        print(f"❌ Erro do LangSmith ao publicar {prompt_id}: {e}")
        return False

    print(f"✓ Prompt publicado: {url}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    _, errors = validate_prompt_structure(prompt_data)

    if not prompt_data.get("tags"):
        errors.append("tags precisa ter ao menos 1 item")

    system_prompt = prompt_data.get("system_prompt", "")
    user_prompt = prompt_data.get("user_prompt", "")

    if "[TODO]" in system_prompt or "[TODO]" in user_prompt:
        errors.append("o prompt ainda contém [TODO]")
    if "{bug_report}" in system_prompt:
        errors.append("{bug_report} não deve aparecer no system_prompt")
    if "{bug_report}" not in user_prompt:
        errors.append("user_prompt precisa conter {bug_report}")

    if system_prompt.strip() and user_prompt.strip():
        try:
            variables = build_prompt_template(prompt_data).input_variables
        except ValueError as e:
            errors.append(f"template inválido: {e}")
        else:
            if variables != ["bug_report"]:
                errors.append(f"bug_report deve ser a única variável, encontradas: {variables}")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DO PROMPT OTIMIZADO")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    prompts = load_yaml(str(PROMPT_PATH))
    prompt_data = (prompts or {}).get(PROMPT_NAME)
    if not prompt_data:
        print(f"❌ Prompt {PROMPT_NAME} não encontrado em {PROMPT_PATH}")
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido, nada foi publicado:")
        for error in errors:
            print(f"   - {error}")
        return 1

    return 0 if push_prompt_to_langsmith(PROMPT_NAME, prompt_data) else 1


if __name__ == "__main__":
    sys.exit(main())
