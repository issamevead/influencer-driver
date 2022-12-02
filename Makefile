.PHONY: lint
lint:
	python -m pylint src

#PHONY docker
.PHONY: build
build:
	docker build -t evead/updated_influencer_driver:dev ./src
.PHONY: run
run:
	docker run -d --name influencer_driver --restart=always -e PROXY="" evead/updated_influencer_driver:dev
.PHONY: clean
clean:
	docker rmi evead/social-api-dev
.PHONY: logs
logs:
	docker logs -f influencer_driver -n 500
.PHONY: remove
remove:
	docker stop influencer_driver
	docker rm influencer_driver
	docker rmi evead/influencer_driver:dev
.PHONY: rmi
rmi:
	docker rmi evead/influencer_driver:dev
