# GCP Compute Engine Start/Stop Cloud Function

Este projeto fornece uma Cloud Function em Python para iniciar ou parar instâncias do Google Compute Engine com base em mensagens do Pub/Sub.

## Funcionalidades
- Acionado por mensagens do Pub/Sub.
- Inicia instâncias ao receber `1`.
- Para instâncias ao receber `0`.
- Lista de instâncias configurável via variável de ambiente.

## Pré-requisitos
- Python 3.11 ou superior
- Conta GCP com permissão de administrador de Compute Engine (`roles/compute.admin`) e acesso ao Pub/Sub.
- GCP Project ID.
- Tópico Pub/Sub configurado.

## Variáveis de Ambiente
Configure as variáveis de ambiente em um arquivo `.env` na raiz do projeto ou diretamente no ambiente:

```dotenv
GCP_PROJECT=seu-projeto-gcp
INSTANCES_ZONES=vm1:zone1,vm2:zone2
```

- `GCP_PROJECT`: ID do projeto GCP.
- `INSTANCES_ZONES`: pares `instancia:zona` separados por vírgula. Exemplo: `vm1:us-central1-a,vm2:us-central1-b`.

## Instalação e Testes Locais
1. Crie e ative um ambiente virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Autentique-se no GCP:
   ```bash
   gcloud auth application-default login
   ```
4. Execute localmente com Functions Framework:
   ```bash
   export GCP_PROJECT=seu-projeto-gcp
   export INSTANCES_ZONES=vm1:us-central1-a,vm2:us-central1-b
   functions-framework --target=le_pubsub --signature-type=cloudevent
   ```
5. Envie uma requisição de teste (Base64 de `1` é `MQ==`):
   ```bash
   curl -X POST \
     -H "Content-Type: application/json" \
     --data '{"message":{"data":"MQ=="}}' \
     http://localhost:8080/
   ```

## Deploy para o Google Cloud Functions
```bash
gcloud functions deploy start_stop_instances \
  --runtime python311 \
  --trigger-topic SEU_TOPICO \
  --entry-point le_pubsub \
  --region SUA_REGIAO \
  --set-env-vars GCP_PROJECT=seu-projeto-gcp,INSTANCES_ZONES=vm1:us-central1-a,vm2:us-central1-b
```

## Agendamento com Cloud Scheduler

Você também pode usar o Cloud Scheduler do GCP para enviar automaticamente mensagens ao tópico Pub/Sub em horários pré-definidos, permitindo iniciar ou parar instâncias de forma programada.

Exemplo de criação de jobs usando `gcloud`:
```bash
# Job para iniciar instâncias diariamente às 08:00 (UTC−03:00)
gcloud scheduler jobs create pubsub start-vms-job \
  --schedule "0 11 * * *" \
  --time-zone "America/Sao_Paulo" \
  --topic SEU_TOPICO \
  --message-body "1"

# Job para parar instâncias diariamente às 20:00 (UTC−03:00)
gcloud scheduler jobs create pubsub stop-vms-job \
  --schedule "0 23 * * *" \
  --time-zone "America/Sao_Paulo" \
  --topic SEU_TOPICO \
  --message-body "0"
```

## Como Funciona
1. Função `le_pubsub` é disparada por evento CloudEvent do Pub/Sub.
2. Decodifica a mensagem Base64 para string e converte para inteiro (1 ou 0).
3. Cria cliente da API Compute Engine.
4. Itera sobre os pares de `instancia:zona` e chama o método `start` ou `stop`.
5. Exibe no log o resultado de cada operação.

## Diagrama de Conexões

Segue um diagrama em ASCII mostrando como o Cloud Scheduler dispara uma mensagem no Pub/Sub, que por sua vez aciona uma Cloud Run Function via Push Subscription:

```
       +----------------+             +------------+             +-----------------------+
       |                |   (1)       |            |   (2)       |                       |
       | Cloud Scheduler|────────────▶|  Pub/Sub   |────────────▶|  Cloud Run Function   |
       |                |  envia msg  |   Topic    |   Push      |                       |
       +----------------+             +------------+             +-----------------------+
```

Legenda dos passos:

1. Scheduler dispara um job periodicamente e publica uma mensagem no tópico Pub/Sub.
2. O tópico Pub/Sub entrega a mensagem pela Push Subscription, que invoca a Cloud Run Function.
