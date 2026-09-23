# Exercise 2: Deploy a Flask App on Minikube using kubectl and YAML

Source exercise: [DevOps-Lab/Exercises/2-Minikube-Kubectl-Flask.md](https://github.com/SunagP/DevOps-Lab/blob/main/Exercises/2-Minikube-Kubectl-Flask.md)

## Files
- [`app.py`](./app.py) — minimal Flask app returning `Hello from Flask on Kubernetes!` on port `15000`.
- [`Dockerfile`](./Dockerfile) — `python:3.8-slim` base, installs Flask, runs `app.py`.
- [`flask-deployment.yaml`](./flask-deployment.yaml) — `Deployment` (1 replica, `imagePullPolicy: Never`)
  + `NodePort` `Service` (port `15000` → container port `15000`), combined into a single manifest
  (the exercise's Step 13 final version).

## What was done
```bash
minikube start
eval $(minikube docker-env)          # point Docker CLI at Minikube's daemon
docker build -t flask-app .
kubectl apply -f flask-deployment.yaml
kubectl get deployments
kubectl get pods -l app=flask-app
kubectl get services
kubectl logs <flask-app-pod>
minikube service flask-app-service --url
curl <returned-url>
```

## Result
- Image `flask-app:latest` built directly inside Minikube's Docker daemon (no registry push needed,
  thanks to `imagePullPolicy: Never`).
- Deployment `flask-app` → `1/1` ready, pod `flask-app-6d58f88547-7lz2c` `Running`.
- Service `flask-app-service` (NodePort) created, mapping `15000:30289/TCP`.
- Pod logs confirm the Flask dev server started on `0.0.0.0:15000`.
- `minikube service flask-app-service --url` produced a local tunnel URL; `curl` against it
  returned **HTTP 200** with body `Hello from Flask on Kubernetes!`.

Full transcript: [run-output.log](./run-output.log) · Raw pod logs: [pod-logs.log](./pod-logs.log)

## Cleanup
```bash
kubectl delete -f flask-deployment.yaml
```
