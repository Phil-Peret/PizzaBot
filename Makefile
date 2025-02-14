IMAGE_NAME = alpine:pizzabot
VENV = venv
PYTHON = python3

build:
	docker build -t $(IMAGE_NAME) .

run:
	docker run --rm $(IMAGE_NAME)

shell:
	docker run --rm -it $(IMAGE_NAME) sh

clean:
	docker rmi $(IMAGE_NAME)

setup-local:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt

activate-venv:
	@echo "Exec: source $(VENV)/bin/activate"

cleanup:
	rm -rf $(VENV)


	

