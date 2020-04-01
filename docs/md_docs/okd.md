# Ansible-bender in OKD

Recently I started experimenting with running ab inside [OpenShift
origin](https://github.com/openshift/origin) — imagine that you'd be able to
build images in your cluster, using Ansible playbooks as definitions.

Openshift by default runs its pods in a
[restrictive](https://blog.openshift.com/understanding-service-accounts-sccs/)
environment. In the proof of concept I was forced to run ab in a privileged
pod. In the end, the whole test suite is passing in that privileged pod.