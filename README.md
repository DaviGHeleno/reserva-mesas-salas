# Reserva de Mesas e Salas

Sistema web para funcionários reservarem mesas de trabalho e salas de reunião
em um prédio de 3 andares (10 mesas e 2 salas por andar).

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

### Regras das salas de reunião
- O funcionário informa a **data**, o **horário de início** e o **horário de fim**.
- Qualquer data de hoje em diante é permitida.
- A reserva **nunca passa do dia**: para usar a sala em dois dias seguidos,
  são necessárias duas reservas, uma para cada dia.
- Não pode haver sobreposição de horários na mesma sala
  (reservas encostadas, como 09:00–10:00 e 10:00–11:00, são permitidas).

### Minhas reservas
Cada funcionário pode ver e cancelar apenas as próprias reservas.

## Como rodar os testes
```bash
pip install -r requirements-dev.txt
pytest
```