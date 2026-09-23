# Exercise 1: Kubernetes Getting Started — Hello Pod

Source exercise: [DevOps-Lab/Exercises/1-Kubernetes-Getting-Started.md](https://github.com/SunagP/DevOps-Lab/blob/main/Exercises/1-Kubernetes-Getting-Started.md)

## Goal
Run a single `nginx` container as a Pod in Kubernetes (Minikube), expose it as a
`NodePort` Service, and access it from a browser/`curl`.

## What was done
```bash
minikube start
kubectl run hello-k8s --image=nginx --port=80
kubectl get pods
kubectl expose pod hello-k8s --type=NodePort --port=80
minikube service hello-k8s --url
```

## Result
- Pod `hello-k8s` reached `Running` / `1/1 Ready`.
- Service `hello-k8s` (NodePort, port 80 → container port 80) was created.
- `minikube service hello-k8s --url` opened a local tunnel
  (`http://127.0.0.1:56431` on this run — port is randomly assigned per run
  since Minikube uses the Docker driver on macOS).
- `curl` against that URL returned **HTTP 200** with the default Nginx welcome page.

Full command transcript: [run-output.log](./run-output.log)

## Cleanup
```bash
kubectl delete service hello-k8s
kubectl delete pod hello-k8s
```
