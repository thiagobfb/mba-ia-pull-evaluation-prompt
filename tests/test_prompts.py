"""
Testes automatizados para validação de prompts.
"""
import re
import sys
from pathlib import Path

import pytest
import yaml
from langchain_core.prompts import ChatPromptTemplate

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture
def prompt_data():
    """Dados do prompt otimizado."""
    return load_prompts(PROMPT_PATH)[PROMPT_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data
        assert prompt_data["system_prompt"].strip()

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        assert re.search(r"Você é um(a)? .*Product Manager", prompt_data["system_prompt"])

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt_data["system_prompt"]
        has_user_story = all(term in system_prompt for term in ("Como", "eu quero", "para que"))
        assert "Markdown" in system_prompt or has_user_story

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt_data["system_prompt"]
        inputs = re.findall(r"^\s*(?:Entrada|Relato)\b.*:", system_prompt, re.MULTILINE)
        outputs = re.findall(r"^\s*(?:Saída|User Story)\b.*:", system_prompt, re.MULTILINE)
        assert min(len(inputs), len(outputs)) >= 2

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        assert "[TODO]" not in PROMPT_PATH.read_text(encoding="utf-8")

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])
        assert len(techniques) >= 2
        assert "Few-shot Learning" in techniques

    def test_prompt_structure_is_valid(self, prompt_data):
        """Verifica a estrutura com a mesma função usada pelo projeto."""
        is_valid, errors = validate_prompt_structure(prompt_data)
        assert is_valid, errors

    def test_prompt_only_bug_report_variable(self, prompt_data):
        """Garante que {bug_report} é a única variável e aparece só no User Prompt."""
        template = ChatPromptTemplate.from_messages([
            ("system", prompt_data["system_prompt"]),
            ("user", prompt_data["user_prompt"]),
        ])
        assert template.input_variables == ["bug_report"]
        assert "{bug_report}" in prompt_data["user_prompt"]
        assert "{bug_report}" not in prompt_data["system_prompt"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
