from ab.builder import BuildahBuilder
from ab.core import AnsibleRunner


class Application:
    def __init__(self, playbook_path, base_image, target_image):
        self.builder = BuildahBuilder(base_image, target_image)
        self.a_runner = AnsibleRunner(playbook_path, self.builder)

    def build(self):
        self.builder.create()
        self.a_runner.build()
        self.builder.commit()
