# Exercise 3: Scaling a Flask App on a Single Node using ReplicaSets

Source exercise: [DevOps-Lab/Exercises/3-Minikube-Scaling-Flask-App-with-Replicasets.md](https://github.com/SunagP/DevOps-Lab/blob/main/Exercises/3-Minikube-Scaling-Flask-App-with-Replicasets.md)

## Files
- [`app.py`](./app.py) — "flash sale" Flask app with `/`, `/buy`, and `/health` routes; `/buy`
  reports which pod (`socket.gethostname()`) served the request, to show load distribution.
- [`Dockerfile`](./Dockerfile) — `python:3.11-slim`, installs Flask + Gunicorn, serves on `:5000`
  via `gunicorn`. (Fixed vs. the source exercise's snippet, which `COPY`s a file named
  `ex3-flash-sale.py` but starts `app:app` — here the file is simply named `app.py` to match.)
- [`flashsale-replicaset.yaml`](./flashsale-replicaset.yaml) — `ReplicaSet` (3 replicas) with
  readiness/liveness probes on `/health` and CPU/memory requests+limits, plus a `ClusterIP`
  `Service`. Added `imagePullPolicy: Never` so it uses the image built directly in Minikube's
  Docker daemon instead of trying to pull `flashsale:1.0` from a registry.

## What was done
```bash
minikube start --nodes=1
eval $(minikube docker-env)
docker build -t flashsale:1.0 .
kubectl apply -f flashsale-replicaset.yaml      # 3 replicas
kubectl get pods -l app=flashsale
kubectl get rs flashsale-rs

kubectl scale rs flashsale-rs --replicas=5
kubectl get rs flashsale-rs
kubectl get pods -l app=flashsale -o wide

kubectl delete pod <one-of-the-pods>
kubectl get pods -l app=flashsale -o wide       # ReplicaSet recreates it

kubectl port-forward svc/flashsale-svc 18080:80
curl http://127.0.0.1:18080/buy                 # x6
curl http://127.0.0.1:18080/health
```

## Results
1. **Initial state:** `flashsale-rs` created 3 pods, all `Running`/`1/1 Ready` within ~8s.
2. **Scale to 5:** `kubectl scale rs flashsale-rs --replicas=5` → RS went from `DESIRED 3` to
   `DESIRED 5`; 2 new pods (`flashsale-rs-vgjbd`, `flashsale-rs-wbpf8`) were scheduled and became
   Ready.
3. **Self-healing:** Deleting pod `flashsale-rs-hjhdq` triggered the ReplicaSet controller to
   immediately create a replacement (`flashsale-rs-cqvt7`), keeping the pod count at 5 —
   confirming the "if a pod fails, the ReplicaSet creates another" behavior from the exercise.
4. **Load distribution / `/buy` requests:** All 6 `curl` calls were served by the *same* pod
   (`flashsale-rs-w8d5n`). This is expected with `kubectl port-forward svc/...` — port-forward
   binds to a single endpoint pod behind the Service for the life of the forwarded connection; it
   is not itself load-balancing. Real load distribution across all 5 pods is what you'd observe
   via `kube-proxy`-routed traffic (e.g. a `NodePort`/`LoadBalancer` Service hit repeatedly from
   outside the cluster, or `kubectl exec` + `curl` from inside another pod), not through a single
   `port-forward` tunnel.
5. All pods ran on the single `minikube` node, as expected for a 1-node cluster.

Full transcript: [run-output.log](./run-output.log)

## Cleanup
```bash
kubectl delete -f flashsale-replicaset.yaml
```
