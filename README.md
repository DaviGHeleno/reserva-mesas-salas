# Reserva de Mesas e Salas

[![CI](https://github.com/DaviGHeleno/reserva-mesas-salas/actions/workflows/ci.yml/badge.svg)](https://github.com/DaviGHeleno/reserva-mesas-salas/actions/workflows/ci.yml)

Sistema web para funcionários reservarem mesas de trabalho e salas de reunião
em um prédio de 3 andares (10 mesas e 2 salas por andar).

**Aplicação em produção:** https://reserva-mesas-salas.onrender.com

## Integrantes
- Davi Guimaraes Heleno | 2023001689

## Descrição do sistema

O prédio tem 3 andares, cada um com 10 mesas (M1-01 a M3-10) e 2 salas de reunião (S1-1 a S3-2).
Os funcionários reservam a mesa onde vão sentar no dia em que forem trabalhar no escritório,
e reservam salas para reuniões.

### Regras das mesas
- A reserva pode ser do **dia inteiro**, só da **manhã** ou só da **tarde**.
- Só é possível reservar **dias úteis** da **semana atual** ou da **semana seguinte**
  (de hoje até a sexta-feira da próxima semana). Datas passadas não são aceitas.
- Ao escolher uma mesa, aparecem apenas os dias em que ela ainda tem algum período livre,
  e o funcionário escolhe quais dias quer reservar.
- Manhã e tarde podem ser de pessoas diferentes; o dia inteiro bloqueia os dois períodos.
- Um funcionário não pode ter duas mesas no mesmo período.
- Uma reserva de vários dias é tudo ou nada: se um dos dias estiver ocupado, nenhum é reservado.

### Regras das salas de reunião
- O funcionário informa a **data**, o **horário de início** e o **horário de fim**.
- Qualquer data de hoje em diante é permitida.
- A reserva **nunca passa do dia**: para usar a sala em dois dias seguidos,
  são necessárias duas reservas, uma para cada dia.
- Não pode haver sobreposição de horários na mesma sala
  (reservas encostadas, como 09:00–10:00 e 10:00–11:00, são permitidas).

### Minhas reservas
Cada funcionário pode ver e cancelar apenas as próprias reservas.

## Tecnologias
- **Python 3.12** e **FastAPI** (back-end e API REST)
- **HTML, CSS e JavaScript** puro (front-end)
- **Arquivo JSON** para guardar as reservas (sem banco de dados)
- **pytest** e **pytest-cov** (testes de unidade, integração e cobertura)
- **Playwright** (testes end-to-end)
- **GitHub Actions** (CI em Linux, macOS e Windows)
- **Render** (deploy)

## Arquitetura
| Arquivo | Responsabilidade |
|---|---|
| `app/domain.py` | Regras de negócio puras: períodos, janela de datas, conflitos de horário |
| `app/repository.py` | Armazenamento das reservas em arquivo JSON |
| `app/services.py` | Casos de uso: reservar, consultar disponibilidade, cancelar |
| `app/main.py` | API HTTP e entrega da página web |
| `app/static/` | Interface (HTML, CSS e JavaScript) |

## Uso de IA
Usamos o Claude (Anthropic) como assistente durante o desenvolvimento para:
- sugerir a arquitetura em camadas (domínio, repositório, serviço e API);
- gerar versões iniciais do código e dos testes, que revisamos, executamos e ajustamos;
- explicar erros e avisos encontrados (por exemplo, a troca de `httpx` por `httpx2`);
- configurar o GitHub Actions e o deploy no Render.

As regras de negócio foram definidas pela equipe, e todo o código foi testado localmente
antes de cada commit.

## Como executar localmente
```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:create_app --factory --reload
```
Abra http://localhost:8000.

## Como rodar os testes
```bash
# testes de unidade e de integração, com cobertura
pytest --cov=app --cov-report=term-missing

# testes end-to-end (instale o navegador uma vez)
python -m playwright install --with-deps chromium
pytest tests/e2e
```

| Tipo | Quantidade | Pasta |
|---|---|---|
| Unidade | 74 | `tests/unit` |
| Integração | 16 | `tests/integration` |
| End-to-end | 5 | `tests/e2e` |