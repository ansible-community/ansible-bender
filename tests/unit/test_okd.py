""" Making sure that ab can be used as a custom builder in okd """

import json
import os

from flexmock import flexmock

from ansible_bender.api import Application
from ansible_bender.okd import build_inside_openshift


# OKD sets an env var BUILD to this VALUE
# oc get --template '{{ (index (index .spec.containers 0).env 0).value }}' pod/ab-in-okd-1-build | jq
# fun fun
BUILD_ENV = {
  "kind": "Build",
  "apiVersion": "build.openshift.io/v1",
  "metadata": {
    "name": "ab-in-okd-1",
    "namespace": "myproject",
    "selfLink": "/apis/build.openshift.io/v1/namespaces/myproject/builds/ab-in-okd-1",
    "uid": "b0f55118-09d8-11e9-8e48-8c164572b096",
    "resourceVersion": "39780",
    "creationTimestamp": "2018-12-27T13:09:49Z",
    "labels": {
      "buildconfig": "ab-in-okd",
      "openshift.io/build-config.name": "ab-in-okd",
      "openshift.io/build.start-policy": "Serial"
    },
    "annotations": {
      "openshift.io/build-config.name": "ab-in-okd",
      "openshift.io/build.number": "1"
    },
    "ownerReferences": [
      {
        "apiVersion": "build.openshift.io/v1",
        "kind": "BuildConfig",
        "name": "ab-in-okd",
        "uid": "afd64f3d-09d8-11e9-8e48-8c164572b096",
        "controller": True
      }
    ]
  },
  "spec": {
    "serviceAccount": "builder",
    "source": {
      "type": "Git",
      "git": {
        "uri": "https://github.com/TomasTomecek/ansible-bender",
        "ref": "master"
      }
    },
    "strategy": {
      "type": "Custom",
      "customStrategy": {
        "from": {
          "kind": "DockerImage",
          "name": "ansible-bender:latest"
        },
        "pullSecret": {
          "name": "builder-dockercfg-mfvxv"
        },
        "env": [
          {
            "name": "AB_BASE_IMAGE",
            "value": "registry.fedoraproject.org/fedora:29"
          },
          {
            "name": "AB_PLAYBOOK_PATH",
            "value": "recipe.yml"
          },
          {
            "name": "OPENSHIFT_CUSTOM_BUILD_BASE_IMAGE",
            "value": "ansible-bender:latest"
          }
        ]
      }
    },
    "output": {
      "to": {
        "kind": "DockerImage",
        "name": "lolzor"
      },
      "pushSecret": {
        "name": "builder-dockercfg-mfvxv"
      }
    },
    "resources": {},
    "postCommit": {},
    "nodeSelector": None,
    "triggeredBy": [
      {
        "message": "Manually triggered"
      }
    ]
  },
  "status": {
    "phase": "New",
    "outputDockerImageReference": "lolzor",
    "config": {
      "kind": "BuildConfig",
      "namespace": "myproject",
      "name": "ab-in-okd"
    },
    "output": {}
  }
}
BUILD_ENV_RAW = json.dumps(BUILD_ENV)


def test_bio(tmpdir):
    database_path = str(tmpdir)
    flexmock(Application, build=lambda build, extra_ansible_args=None: True)
    application = Application(db_path=database_path, debug=True)

    ose = os.environ
    ose["BUILD"] = BUILD_ENV_RAW
    ose["AB_PLAYBOOK_PATH"] = "asdqwe.yml"
    ose["AB_BASE_IMAGE"] = "pancake"
    flexmock(os, environ=ose)
    try:
        build_inside_openshift(application)
    finally:
        application.clean()
