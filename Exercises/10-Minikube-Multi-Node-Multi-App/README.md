# Exercise 10: Multi-Node Kubernetes Cluster with Multiple Applications and ReplicaSets

Source exercise: [DevOps-Lab/Exercises/10-Minikube-Multi-Node-Multi-App-Minikube-Deployment.md](https://github.com/SunagP/DevOps-Lab/blob/main/Exercises/10-Minikube-Multi-Node-Multi-App-Minikube-Deployment.md)

This exercise models an e-commerce platform with two Flask services on a **3-node Minikube
cluster**. **Product Catalog** (AppA) runs 2 replicas and **Shopping Cart** (AppB) runs 3. A
*required* pod anti-affinity rule (`topologyKey: kubernetes.io/hostname`) forces each replica of
a service onto a different node.

## Files
| File | Purpose |
|---|---|
| [`product_catalog.py`](./product_catalog.py) / [`Dockerfile.product`](./Dockerfile.product) | `GET /products` → list of 3 products |
| [`shopping_cart.py`](./shopping_cart.py) / [`Dockerfile.shopping`](./Dockerfile.shopping) | `GET /cart`, `POST /cart` (in-memory list) |
| [`product_catalog_deployment.yaml`](./product_catalog_deployment.yaml) | Deployment, 2 replicas, required anti-affinity, `imagePullPolicy: Never` |
| [`shopping_cart_deployment.yaml`](./shopping_cart_deployment.yaml) | Deployment, 3 replicas, required anti-affinity, `imagePullPolicy: Never` |
| [`product_catalog_service.yaml`](./product_catalog_service.yaml) / [`shopping_cart_service.yaml`](./shopping_cart_service.yaml) | NodePort Services on port 80 |

## Changes vs. the source exercise
- **Shopping Cart namespace fixed.** The source puts the Deployment in
  `namespace: devops-exercise`, which is never created, so `kubectl apply` fails. Its Service is
  in `default`, so it would have no pods behind it anyway. Both are in `default` here.
- **No `--force`.** The source passes it because it runs Minikube as root on Linux. On macOS,
  Docker Desktop doesn't need it.
- **Registry add-on skipped (Step 1b).** The manifests use `imagePullPolicy: Never` with
  `minikube image load`, which copies the images into every node (verified below). The registry
  add-on is never actually used in the exercise.
- **`--memory=1800 --cpus=2` per node**, so 3 nodes fit in Docker Desktop's 8 GB.
- **`--base-image=gcr.io/k8s-minikube/kicbase:v0.0.49`.** This is a local workaround, not an
  exercise change. The Mac's disk filled up while Docker was pulling the default `v0.0.50`
  base image. That left a corrupted layer (every binary in `/usr/local/bin` was 0 bytes), so node
  containers died with `exec format error`, and Docker kept reusing the bad layer even after
  re-pulls. The previous kicbase version doesn't share that layer and ran normally (Kubernetes
  v1.35.1).

## What was done
```bash
minikube start --nodes 3 -p devops-multinode --driver=docker --memory=1800 --cpus=2 \
  --base-image=gcr.io/k8s-minikube/kicbase:v0.0.49
docker build -t product-catalog:latest -f Dockerfile.product .
docker build -t shopping-cart:latest -f Dockerfile.shopping .
minikube -p devops-multinode image load product-catalog:latest
minikube -p devops-multinode image load shopping-cart:latest
kubectl apply -f product_catalog_deployment.yaml -f shopping_cart_deployment.yaml
kubectl apply -f product_catalog_service.yaml -f shopping_cart_service.yaml
kubectl get pods -o wide
minikube -p devops-multinode service product-catalog-service --url   # keep running (tunnel)
minikube -p devops-multinode service shopping-cart-service --url
curl <catalog-url>/products
curl <cart-url>/cart
curl -X POST <cart-url>/cart -H "Content-Type: application/json" -d '{"id": 1, "name": "Laptop", "quantity": 1}'
```

## Results
1. **Cluster:** 3 nodes all `Ready`: `devops-multinode` (control-plane), `-m02` and `-m03`.
   Both images were present on all three nodes after `image load`.
2. **Distribution (Step 8):** every replica is on a different node, as required.
   ```
   product-catalog   devops-multinode-m02
   product-catalog   devops-multinode-m03
   shopping-cart     devops-multinode
   shopping-cart     devops-multinode-m02
   shopping-cart     devops-multinode-m03
   ```
   Deployments showed `2/2` and `3/3`, and both NodePort Services were created.
3. **curl tests (Step 10):** all three responses match the exercise:
   - `GET /products` returned Laptop, Phone and Headphones
   - `GET /cart` returned `[]`
   - `POST /cart` returned `[{"id":1,"name":"Laptop","quantity":1}]`

### Extra checks
4. **The cart is not shared between replicas.** After that one POST, 9 repeated `GET /cart`
   calls returned the item 3 times and `[]` 6 times. Querying each pod directly showed only the
   pod on `m03` holds the item. `cart = []` is per-process memory, and the Service spreads
   requests across the 3 pods. A real cart needs shared state (e.g. Redis or a database) or
   session affinity.
5. **Node failure:** drained `devops-multinode-m03` to simulate losing a node.
   - **Product Catalog** rescheduled its evicted pod onto the control-plane node and stayed at
     `2/2`.
   - **Shopping Cart** dropped to `2/3`. Its replacement pod stayed **Pending** with
     `0/3 nodes are available: 1 node(s) had untolerated taint(s), 2 node(s) didn't match pod anti-affinity rules`.
     With *required* anti-affinity, 3 replicas need 3 schedulable nodes.
   - **Both services kept answering HTTP 200** during the outage, which is the availability goal
     of the storyboard.
   - After `kubectl uncordon`, the pending pod was scheduled on `m03` and the deployment was
     `3/3` again.
   - Using `preferredDuringSchedulingIgnoredDuringExecution` would let the third replica double
     up on a surviving node instead of waiting.

Full transcript: [run-output.log](./run-output.log)

## Cleanup
```bash
minikube -p devops-multinode stop     # or: minikube delete -p devops-multinode
```
