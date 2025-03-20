COMPOSE_FILE = docker-compose.yml
VENV = venv
PYTHON = python3
ENV_FILE = .env
SERVICE = bot

up:
	docker-compose -f $(COMPOSE_FILE) up

upd:
	docker-compose -f $(COMPOSE_FILE) up -d

down:
	docker-compose -f $(COMPOSE_FILE) down

restart: down up

status:
	docker-compose -f $(COMPOSE_FILE) ps

logs:
	docker-compose logs -f $(SERVICE)

init-venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt

shell:
	docker-compose -f $(COMPOSE_FILE) exec $(SERVICE) sh

run-local:
	python src/main.py

source-venv:
	@echo "Exec: source $(VENV)/bin/activate"

remove-venv:
	rm -rf $(VENV)

clean:
	docker system prune -af
	docker volume prune -f
