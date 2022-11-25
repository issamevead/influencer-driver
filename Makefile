.PHONY: lint
lint:
	python -m pylint src

#PHONY docker
.PHONY: build
build:
	docker build -t evead/influencer_driver:dev ./src
.PHONY: run
run:
	docker run -d --name instagram_robot --restart=always -e PROXY="" evead/influencer_driver:dev
.PHONY: clean
clean:
	docker rmi evead/social-api-dev
.PHONY: logs
logs:
	docker logs -f instagram_robot -n 500
.PHONY: remove
remove:
	docker stop instagram_robot
	docker rm instagram_robot
	docker rmi evead/influencer_driver:dev
.PHONY: rmi
rmi:
	docker rmi evead/influencer_driver:dev
