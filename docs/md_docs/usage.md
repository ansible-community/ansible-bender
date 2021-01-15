# Usage

Typing `ansible-bender` can take some time, consider adding an alias into your
shell rc file:
```
alias ab="ansible-bender"
```

### Building images

There is a simple playbook present in the root of this repository to showcase the functionality:
```bash
$ ansible-bender build ./simple-playbook.yaml

PLAY [Demonstration of ansible-bender functionality] ****************************************

TASK [Gathering Facts] **********************************************************************
ok: [a-very-nice-image-20190302-153257279579-cont]

TASK [Run a sample command] *****************************************************************
changed: [a-very-nice-image-20190302-153257279579-cont]
caching the task result in an image 'a-very-nice-image-20193302-153306'

TASK [Stat a file] **************************************************************************
ok: [a-very-nice-image-20190302-153257279579-cont]
caching the task result in an image 'a-very-nice-image-20193302-153310'

PLAY RECAP **********************************************************************************
a-very-nice-image-20190302-153257279579-cont : ok=3    changed=1    unreachable=0    failed=0

Getting image source signatures

Skipping blob 767f936afb51 (already present): 4.46 MiB / 4.46 MiB [=========] 0s

Skipping blob b211a7fc6e85 (already present): 819.00 KiB / 819.00 KiB [=====] 0s

Skipping blob 8d092d3e44bb (already present): 67.20 MiB / 67.20 MiB [=======] 0s

Skipping blob 767f936afb51 (already present): 4.46 MiB / 4.46 MiB [=========] 0s

Skipping blob b211a7fc6e85 (already present): 819.00 KiB / 819.00 KiB [=====] 0s

Skipping blob 8d092d3e44bb (already present): 67.20 MiB / 67.20 MiB [=======] 0s

Skipping blob 492c5c55da84 (already present): 4.50 KiB / 4.50 KiB [=========] 0s

Skipping blob 6f55b6e55d8a (already present): 6.15 MiB / 6.15 MiB [=========] 0s

Skipping blob 80ea48511c5d (already present): 1021.00 KiB / 1021.00 KiB [===] 0s

Copying config 6b6dc5878fb2: 0 B / 5.15 KiB [----------------------------------]
Copying config 6b6dc5878fb2: 5.15 KiB / 5.15 KiB [==========================] 0s
Writing manifest to image destination
Storing signatures
6b6dc5878fb2c2c10099adbb4458c2fc78cd894134df6e4dee0bf8656e93825a
Image 'a-very-nice-image' was built successfully \o/
```

This is how the playbook looks:
```yaml
---
- name: Demonstration of ansible-bender functionality
  hosts: all
  vars:
    ansible_bender:
      base_image: python:3-alpine

      working_container:
        volumes:
          - '{{ playbook_dir }}:/src'

      target_image:
        name: a-very-nice-image
        working_dir: /src
        environment:
          FILE_TO_PROCESS: README.md
  tasks:
  - name: Run a sample command
    command: 'ls -lha /src'
  - name: Stat a file
    stat:
      path: "{{ lookup('env','FILE_TO_PROCESS') }}"
```

As you can see, the whole build processed is configured by the variable
`ansible_bender`.
The list of known variables by ansible-bender is detailed in the document
[configuration.md](docs/configuration.md).

If we rerun the build again, we can see that ab loads every task from cache:
```bash
$ ansible-bender build ./simple-playbook.yaml

PLAY [Demonstration of ansible-bender functionality] ****************************************

TASK [Gathering Facts] **********************************************************************
ok: [a-very-nice-image-20190302-153526013757-cont]

TASK [Run a sample command] *****************************************************************
loaded from cache: '7c69668c42987446cc78adbf6620fc2faf90ad10c3497662fe38940dd6de998f'
skipping: [a-very-nice-image-20190302-153526013757-cont]

TASK [Stat a file] **************************************************************************
loaded from cache: '4a4f54285928c03eea65745ee9feead88026c780a40126d94e79d5842bcdbe62'
skipping: [a-very-nice-image-20190302-153526013757-cont]

PLAY RECAP **********************************************************************************
a-very-nice-image-20190302-153526013757-cont : ok=1    changed=0    unreachable=0    failed=0

Getting image source signatures

Skipping blob 767f936afb51 (already present): 4.46 MiB / 4.46 MiB [=========] 0s

Skipping blob b211a7fc6e85 (already present): 819.00 KiB / 819.00 KiB [=====] 0s

Skipping blob 8d092d3e44bb (already present): 67.20 MiB / 67.20 MiB [=======] 0s

Skipping blob 492c5c55da84 (already present): 4.50 KiB / 4.50 KiB [=========] 0s
Skipping blob 767f936afb51 (already present): 4.46 MiB / 4.46 MiB [=========] 0s
Skipping blob 6f55b6e55d8a (already present): 6.15 MiB / 6.15 MiB [=========] 0s
Skipping blob b211a7fc6e85 (already present): 819.00 KiB / 819.00 KiB [=====] 0s
Skipping blob 80ea48511c5d (already present): 1021.00 KiB / 1021.00 KiB [===] 0s
Skipping blob 8d092d3e44bb (already present): 67.20 MiB / 67.20 MiB [=======] 0s
Skipping blob 5f70bf18a086 (already present): 1.00 KiB / 1.00 KiB [=========] 0s
Skipping blob 492c5c55da84 (already present): 4.50 KiB / 4.50 KiB [=========] 0s

Skipping blob 6f55b6e55d8a (already present): 6.15 MiB / 6.15 MiB [=========] 0s

Skipping blob 80ea48511c5d (already present): 1021.00 KiB / 1021.00 KiB [===] 0s

Skipping blob 5f70bf18a086 (already present): 1.00 KiB / 1.00 KiB [=========] 0s

Copying config 354752b97084: 0 B / 5.26 KiB [----------------------------------]
Copying config 354752b97084: 5.26 KiB / 5.26 KiB [==========================] 0s
Writing manifest to image destination
Storing signatures
354752b97084fcf349a28a2f66839d270e728559883dd1edb5ec22e8c9c6adb9
Image 'a-very-nice-image' was built successfully \o/
```


### Listing builds

We can list builds we have done:
```bash
$ ansible-bender list-builds
  BUILD ID  IMAGE NAME         STATUS    DATE                        BUILD TIME
----------  -----------------  --------  --------------------------  --------------
         1  a-very-nice-image  done      2019-03-02 16:07:47.471912  13 minutes
         2  a-very-nice-image  done      2019-03-02 16:07:58.858699  7 minutes
```


### Getting logs of a build

Wanna check build logs sometime later? No problem!
```bash
$ ansible-bender get-logs 2

PLAY [Demonstration of ansible-bender functionality] *********************************

TASK [Gathering Facts] ***************************************************************
ok: [a-very-nice-image-20190302-160751828671-cont]

TASK [Run a sample command] **********************************************************
loaded from cache: 'cd27cfb71a161f3333232b97cc6b2a89354ff52de71bce9058c52cdf536735f9'
skipping: [a-very-nice-image-20190302-160751828671-cont]

TASK [Stat a file] *******************************************************************
loaded from cache: '89ba4efc31358d688f035bf8159d900f1552314f0af6bf6c338b4897da593ccf'
skipping: [a-very-nice-image-20190302-160751828671-cont]

PLAY RECAP ***************************************************************************
a-very-nice-image-20190302-160751828671-cont : ok=1    changed=0    unreachable=0    failed=0
```


### Locating built images with podman

Once they are built, you can use them with podman right away:
```bash
$ podman images a-very-nice-image
REPOSITORY                    TAG      IMAGE ID       CREATED         SIZE
localhost/a-very-nice-image   latest   5202048d9a0e   2 minutes ago   83.5 MB
```
