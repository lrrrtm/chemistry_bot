# GHCR Deploy

## Что уже настроено

- При пуше в `master` GitHub Actions:
  - прогоняет тесты и проверки
  - собирает Docker image
  - пушит image в `ghcr.io`
  - подключается по SSH к серверу
  - делает `docker compose pull`
  - поднимает контейнеры без локальной сборки на VPS

## Что нужно добавить в GitHub Secrets

- `SSH_HOST`
- `SSH_PORT`
- `SSH_USER`
- `SSH_KEY`
- `DEPLOY_PATH`

Если GHCR package приватный, добавьте ещё:

- `GHCR_USERNAME`
- `GHCR_TOKEN`

`GHCR_TOKEN` должен уметь читать packages.

## Что должно быть на сервере

- Репозиторий уже склонирован в `${DEPLOY_PATH}`
- Есть актуальный `.env`
- Docker и Docker Compose установлены

## Какой compose используется

На сервере deploy использует:

- `docker-compose.yml`
- `docker-compose.prod.yml`

`docker-compose.prod.yml` переключает `api`, `bot` и `backup` на image из GHCR, поэтому серверу больше не нужно собирать проект локально.
