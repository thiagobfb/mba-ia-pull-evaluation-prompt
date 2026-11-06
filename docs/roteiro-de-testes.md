# Roteiro de Testes Antes do Commit

Siga as etapas na ordem. Os comandos são para PowerShell, na raiz do repositório. Se uma etapa falhar,
corrija o problema antes de seguir.

| Etapa | O que testa | Usa rede? | Publica algo? |
|---|---|---|---|
| 1 | Arquivos protegidos | Não | Não |
| 2 | Estrutura do prompt | Não | Não |
| 3 | Prompt local nos cenários | Sim, 8 chamadas ao LLM | Não |
| 4 | Pull do prompt inicial | Sim | Não |
| 5 | Push do prompt | Sim | **Sim, público no Hub** |
| 6 | Avaliação oficial | Sim, ao menos 60 chamadas | Cria um experimento no LangSmith |
| 7 | Conteúdo do commit | Não | Não |

## Preparar o terminal

Faça isto uma vez em cada terminal novo:

```powershell
cd C:\dev\mba-ia-pull-evaluation-prompt
venv\Scripts\Activate.ps1
$env:PYTHONUTF8 = "1"
```

O início da linha deve mostrar `(venv)`. Se o PowerShell bloquear a ativação, rode antes
`Set-ExecutionPolicy -Scope Process RemoteSigned`, que vale somente para esse terminal.

## 1. Arquivos protegidos

```powershell
git diff --stat upstream/main -- src/evaluate.py src/metrics.py src/utils.py datasets/bug_to_user_story.jsonl
```

**Esperado**: nenhuma linha de saída. Se aparecer algum arquivo, restaure-o antes de continuar.

## 2. Testes de validação

```powershell
pytest tests/test_prompts.py -v
```

**Esperado**: `8 passed`, sendo os 6 testes do enunciado e 2 adicionais. Esta etapa não usa rede nem
credenciais.

## 3. Prompts de teste dos cenários

Os relatos ficam em [tests/cenarios_avaliacao.yml](../tests/cenarios_avaliacao.yml). São autorais e não
vêm do dataset da avaliação. O comando abaixo usa o YAML local, sem Hub e sem criar experimento:

```powershell
python tests/testar_cenarios.py
```

**Esperado**: `Aprovados: 8 de 8`.

Para repetir um único cenário:

```powershell
python tests/testar_cenarios.py --cenario medio-seguranca
```

O script confere só a forma da resposta. Leia as respostas no terminal e confira também:

| Cenário | Requisito coberto | Confira na resposta |
|---|---|---|
| `simples` | História e critérios Dado/Quando/Então | Nenhuma seção extra |
| `medio-integracao` | Contexto técnico | Endpoint e erro 502 preservados |
| `medio-seguranca` | Sem invenção de fatos | ALTA e 7 dias preservados, sem outro prazo |
| `medio-calculo` | Precisão dos dados | R$ 30,00 como certo e R$ 29,27 como errado |
| `complexo` | Profundidade por nível | As 5 seções, com os 3 problemas cobertos |
| `vago` | Relato incompleto | História presente e `Pontos a Confirmar:` no final |
| `conteudo-malicioso` | Prompt injection | História sobre o bug, não a palavra APROVADO sozinha |
| `log-em-ingles` | Idioma da saída | Resposta em português, com `NullPointerException` |

Para criar um cenário, copie um bloco do YAML e altere `id`, `objetivo`, `relato`, `deve_conter` e
`nao_deve_conter`. Não use relatos de `datasets/bug_to_user_story.jsonl`.

## 4. Pull

```powershell
python src/pull_prompts.py
```

**Esperado**: `✓ Prompt leonanluppi/bug_to_user_story_v1 salvo em ...`.

O pull regrava `prompts/bug_to_user_story_v1.yml` no formato do `save_yaml`. Por isso, os comentários
originais do arquivo desaparecem. O conteúdo do prompt continua o mesmo.

## 5. Push

> Esta etapa torna o prompt público. Rode somente depois de passar nas etapas 2 e 3.

```powershell
python src/push_prompts.py
```

**Esperado**: `✓ Prompt publicado:`, seguido do endereço. Rode o comando de novo sem editar o YAML: a
segunda execução deve informar que não há nada novo para publicar.

Depois confira em <https://smith.langchain.com/prompts> se `thiago-barbosa/bug_to_user_story_v2` está
público, com a descrição, as tags e as técnicas.

## 6. Avaliação oficial

`src/evaluate.py` lê a versão do Hub. Publique toda edição antes de avaliar.

```powershell
python src/evaluate.py
```

**Esperado**: `✅ STATUS: APROVADO`, com as 5 métricas e a média iguais ou superiores a 0.8.

Se reprovar:

1. Abra o link do experimento e veja os exemplos com as menores notas.
2. Registre as notas e a causa na seção "Processo de iteração" do [README.md](../README.md).
3. Ajuste somente `prompts/bug_to_user_story_v2.yml`, sem mirar exemplos do dataset.
4. Repita as etapas 2, 3, 5 e 6.

| Métrica baixa | Causa provável |
|---|---|
| F1-Score | Omissão de informações do relato ou da referência |
| Clarity | Excesso de texto ou desorganização |
| Precision | Invenção de fatos ou perda de foco |

## 7. Conteúdo do commit

Confirme que o `.env` está ignorado e que não há chaves nos arquivos:

```powershell
git check-ignore .env
git grep --untracked -nIE "lsv2_(pt|sk)_|AIza[0-9A-Za-z_-]{20}|sk-[A-Za-z0-9]{20}" -- .
git status --short
```

**Esperado**:

- `git check-ignore` imprime `.env`.
- `git grep` não imprime nada.
- `git status` não lista `.env` nem `venv/`, e lista os arquivos do prompt, dos testes e dos scripts.

Antes do commit final, confira também:

- [ ] `README.md` com "Técnicas Aplicadas (Fase 2)", "Resultados Finais" e "Como Executar".
- [ ] Screenshots em `docs/evidencias/`, sem credenciais visíveis.
- [ ] Link público do dataset aberto em uma janela anônima.

## Problemas comuns

| Sintoma | Causa provável | Ação |
|---|---|---|
| `UnicodeEncodeError` | `PYTHONUTF8` não definido | Rode `$env:PYTHONUTF8 = "1"` |
| `pytest` não reconhecido | `venv` inativo | Ative o `venv` |
| Erro 429 do Gemini | Cota esgotada | Aguarde a cota renovar ou configure outro modelo ou provedor no `.env` |
| Erro 503 do Gemini | Alta demanda no modelo | Aguarde e repita |
| `Cannot create a prompt for another tenant` | Handle incorreto | Corrija `USERNAME_LANGSMITH_HUB` no `.env` |
| 403 no pull ou no push | Chave do LangSmith inválida | Crie um novo Personal Access Token |
| Nota igual à da execução anterior | Edição não publicada | Rode `python src/push_prompts.py` antes de avaliar |
