"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.prompts import HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPT_ID = "leonanluppi/bug_to_user_story_v1"
PROMPT_KEY = "bug_to_user_story_v1"
OUTPUT_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v1.yml"


def pull_prompts_from_langsmith():
    """
    Baixa o prompt semente e o grava em prompts/bug_to_user_story_v1.yml.

    O arquivo só é gravado depois de confirmar que o System Prompt veio do Hub,
    para preservar a cópia local em caso de falha.

    Returns:
        Caminho do arquivo gravado

    Raises:
        ValueError: Se o prompt não tiver mensagem de sistema
        OSError: Se o arquivo não puder ser gravado
    """
    prompt = Client().pull_prompt(PROMPT_ID, dangerously_pull_public_prompt=True)

    system_prompt = ""
    user_prompt = ""
    for message in prompt.messages:
        if isinstance(message, SystemMessagePromptTemplate):
            system_prompt = message.prompt.template
        elif isinstance(message, HumanMessagePromptTemplate):
            user_prompt = message.prompt.template

    if not system_prompt.strip():
        raise ValueError(f"O prompt {PROMPT_ID} não tem mensagem de sistema")

    data = {
        PROMPT_KEY: {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "version": "v1",
            "created_at": "2025-01-15",
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    if not save_yaml(data, str(OUTPUT_PATH)):
        raise OSError(f"Não foi possível gravar {OUTPUT_PATH}")

    return OUTPUT_PATH


def main():
    """Função principal"""
    print_section_header("PULL DO PROMPT INICIAL")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    try:
        output_path = pull_prompts_from_langsmith()
    except Exception as e:
        print(f"❌ Falha ao baixar {PROMPT_ID}: {e}")
        print("\nVerifique LANGSMITH_API_KEY no .env e a sua conexão com a internet.")
        print("O arquivo local não foi alterado.")
        return 1

    print(f"✓ Prompt {PROMPT_ID} salvo em {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
