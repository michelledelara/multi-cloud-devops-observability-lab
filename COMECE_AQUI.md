# Guia de execução

Este projeto reúne infraestrutura como código, entrega de aplicações e observabilidade. A aplicação é pequena de propósito: o objeto de engenharia é o sistema que a provisiona, executa, monitora e verifica.

## Preparar o ambiente

1. Extraia o ZIP e abra a pasta `multi-cloud-devops-observability-lab` no VS Code.
2. Instale Python 3.12 e Docker Desktop com containers Linux. No Windows, habilite a integração com WSL2 para executar os comandos Bash e o Ansible.
3. No terminal, entre na raiz do projeto, onde está `compose.yaml`.
4. Execute `docker version`, `docker compose version` e `python --version`.

O Docker precisa estar iniciado. As portas 8080, 3000, 9090 e 9093 devem estar livres.

## Iniciar o sistema

```bash
python scripts/prepare_env.py
docker compose up -d --build
python scripts/smoke.py
```

O primeiro comando cria uma senha local para o Grafana. Abra `.env` no seu computador para consultar essa senha. Entre em `http://localhost:3000` com usuário `admin` e abra o dashboard **Multi-cloud DevOps Observability Lab**.

```bash
python scripts/traffic.py --mode normal --seconds 60
```

Observe requisições por segundo, latência, uso do processo e logs. Os gráficos usam dados da aplicação em execução. O teste de integração verifica se as métricas e os logs chegaram aos destinos.

## Percorrer o código

| Pergunta de engenharia | Arquivos |
|---|---|
| O que a aplicação expõe? | `app/main.py` e `tests/test_app.py` |
| Como ela é empacotada? | `docker/Dockerfile` e `compose.yaml` |
| Como são medidas as requisições? | `observability/prometheus/` |
| Como os logs chegam ao dashboard? | `observability/alloy/`, `loki/` e `grafana/` |
| Como replicas e atualizações funcionam? | `kubernetes/` e `kustomization.yaml` |
| Como são criadas as redes? | `terraform/azure/`, `terraform/oci/`, `cloudformation/aws/` |
| O que o Ansible configura? | `ansible/playbook.yml` e `ansible/templates/` |
| O que é automatizado no commit? | `.github/workflows/ci.yml` |

## Provocar e investigar um incidente

Em `.env`, altere `ENABLE_FAULTS=false` para `ENABLE_FAULTS=true`, recrie a API e gere erros:

```bash
docker compose up -d --force-recreate api
python scripts/traffic.py --mode errors --seconds 240
```

Abra os alertas em `http://localhost:9090/alerts`. Consulte no Grafana:

```logql
{job="lab-api"} | json | status >= 500
```

Ao terminar, devolva `ENABLE_FAULTS=false` e recrie a API. A recuperação do alerta depende da janela de avaliação, descrita em `docs/runbooks.md`.

## Executar os demais componentes

- Kubernetes: siga `docs/kubernetes.md`; o script usa um cluster kind local.
- Azure, OCI e AWS: siga `docs/cloud-deployment.md` e revise cada plano com sua própria conta autenticada.
- Ansible: o playbook padrão escreve em `.lab-managed/`, dentro do projeto. Os arquivos podem ser usados com `docker run --env-file .lab-managed/app.env ...`.
- CI/CD: os arquivos estão prontos para versionamento; as execuções e seus resultados ficam na plataforma em que o repositório for publicado.

## Colocar no GitHub

Crie um repositório vazio chamado `multi-cloud-devops-observability-lab`. No terminal da pasta extraída:

```bash
git init
git add .
git status
```

Confirme que `.env`, chaves, arquivos `.tfvars` reais e estados do Terraform não estão entre os arquivos preparados. O `.gitignore` já cobre esses itens.

```bash
git commit -m "Add multi-cloud infrastructure and observability lab"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/multi-cloud-devops-observability-lab.git
git push -u origin main
```

Substitua `SEU_USUARIO` pelo seu usuário. O commit aciona a validação definida em GitHub Actions; publicação de imagem é uma ação manual separada. Não há publicação automática em contas cloud.

## Encerrar

```bash
docker compose down
kind delete cluster --name multicloud-lab
```

Use o procedimento específico de `destroy` ou exclusão de stack para remover infraestrutura cloud criada por você. Encerrar containers locais não remove recursos de nuvem.
