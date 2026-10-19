# Jenkins LTS + Docker CLI, so pipeline steps can drive the host's Docker daemon
# through the mounted /var/run/docker.sock
FROM jenkins/jenkins:lts
COPY --from=docker:29-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker:29-cli /usr/local/libexec/docker/cli-plugins/docker-buildx /usr/local/libexec/docker/cli-plugins/docker-buildx
