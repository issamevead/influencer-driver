.PHONY: lint
lint:
	python -m pylint src

#PHONY docker
.PHONY: build
build:
	docker build -t evead/updated_influencer_driver:dev ./src
.PHONY: run
run:
	docker run -d --name influencer_driver --dns 8.8.8.8 --dns 1.1.1.1 --restart=always -e FFPROFILE="/src/ffprofile" -e PATH_PROFILES="/src/profiles_creds.txt" -e PROFILES_CREDTS="/src/profiles_creds.json" -e FIREFOX_PATH="/usr/lib/firefox/firefox" -e LOCAL_CONF_PATH="/src/proxychains.conf" -e MAIN="main.py" evead/updated_influencer_driver:dev
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

.PHONY: test
test:
	docker run --rm --name influencer_driver --dns 8.8.8.8 --dns 1.1.1.1 -e FFPROFILE="/src/ffprofile" -e PATH_PROFILES="/src/profiles_creds.txt" -e PROFILES_CREDTS="/src/profiles_creds.json" -e FIREFOX_PATH="/usr/lib/firefox/firefox" -e MAIN="main.py" evead/updated_influencer_driver:dev 
.PHONY: clean
clean:
	docker images | grep "<none>" | awk '{print $3}' | xargs docker rmi --force
.PHONY: enter
enter:
	docker exec -it influencer_driver bash
	