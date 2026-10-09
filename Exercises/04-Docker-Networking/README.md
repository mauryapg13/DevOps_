# Exercise 4: Docker Networking with Multiple Containers

Source exercise: [DevOps-Lab/Exercises/4-Docker-Networking.md](https://github.com/SunagP/DevOps-Lab/blob/main/Exercises/4-Docker-Networking.md)

## Files
- [`app.py`](./app.py) — Flask REST API with an `/about` route on port `5001`. Changed
  `app.run(...)` to bind `host='0.0.0.0'`; the source snippet binds Flask's default `127.0.0.1`,
  so `-p 5001:5001` would publish a port nothing inside the container is listening on externally.
- [`requirements.txt`](./requirements.txt) — `Flask==2.0.1` as in the source, plus
  `Werkzeug==2.0.3`. Without the pin pip pulls Werkzeug 3.x, which removed `url_quote` and makes
  Flask 2.0.1 crash on import.
- [`Dockerfile`](./Dockerfile) — `python:3.9-slim` as in the source, plus `iputils-ping`
  (the slim image has no `ping`, which Task 5 needs).

## What was done
```bash
docker network create --driver bridge my-bridge-net
docker network ls
docker build -t flask-api .

docker run -d --name mysql --net=my-bridge-net -e MYSQL_ROOT_PASSWORD=rootpass mysql:latest
docker run -d --name redis --net=my-bridge-net redis:latest
docker run -d --name flask --net=my-bridge-net -p 5001:5001 flask-api
docker network inspect my-bridge-net

docker exec flask ping -c 3 mysql
docker exec flask ping -c 3 redis
curl http://localhost:5001/about

docker stop mysql redis flask && docker rm mysql redis flask
docker network rm my-bridge-net
```
`MYSQL_ROOT_PASSWORD` was added to the MySQL run command. The source exercise omits it, and
the official `mysql` image exits right away without a root-password env var, so `ping mysql`
would fail because the container is no longer running.

## Results
1. **Network:** `my-bridge-net` was created with subnet `172.18.0.0/16` and gateway `172.18.0.1`.
   After the containers started, `docker network inspect` listed all three:
   `mysql` → `172.18.0.2`, `redis` → `172.18.0.3`, `flask` → `172.18.0.4`.
2. **Name-based connectivity:** From inside `flask`, `ping mysql` and `ping redis` resolved
   through Docker's embedded DNS (`mysql.my-bridge-net`, `redis.my-bridge-net`) with 0% packet
   loss. A TCP check from the Flask container also reached the service ports (`mysql:3306` and
   `redis:6379` were open), and `redis-cli -h redis ping` returned `PONG`.
3. **Port publishing:** `curl http://localhost:5001/about` from the Mac host returned the API's
   JSON, which confirms that `-p 5001:5001` works.
4. **Contrast with the default `bridge`:** A container on Docker's default `bridge` network
   could not resolve `mysql` (`Name or service not known`). Automatic container-name DNS works
   only on user-defined networks, which is the reason to create `my-bridge-net`.
5. **Cleanup:** All three containers and `my-bridge-net` were removed.

Full transcript: [run-output.log](./run-output.log)

## Questions & Answers
1. **Purpose of `--net`?** It attaches the container to a specific Docker network instead of the
   default `bridge`.
2. **How do containers on the same network communicate?** By container name (resolved by
   Docker's embedded DNS server at `127.0.0.11` on user-defined networks) or by IP address.
3. **Bridge vs host network?** A bridge network gives each container its own network namespace
   and private IP behind a virtual switch, and ports must be published with `-p`. A host network
   shares the host's network stack directly, so there is no isolation and no port mapping.
4. **Exposing a port to the host?** Use `-p <host_port>:<container_port>`, e.g. `-p 5001:5001`.
   The app must also listen on `0.0.0.0` inside the container.
