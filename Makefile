IMAGE_NAME=alpine:pizzabot

build:
	docker build -t $(IMAGE_NAME) .

run:
	docker run --rm $(IMAGE_NAME)

shell:
	docker run --rm -it $(IMAGE_NAME) sh

clean:
	docker rmi $(IMAGE_NAME)