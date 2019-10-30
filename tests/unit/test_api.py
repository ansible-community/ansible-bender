import pytest

from ansible_bender.core import AnsibleRunner
from flexmock import flexmock

from ansible_bender.builders.buildah_builder import BuildahBuilder


@pytest.mark.parametrize("is_base_present,times_called", (
        (False, 1),
        (True, 0)
))
def test_build_pulls_base_img_if_not_present(application, build, is_base_present, times_called):
    build.base_image = "very-good/and-warm:mead"

    B = flexmock(BuildahBuilder)
    B.should_receive("sanity_check").and_return(None)
    B.should_receive("is_base_image_present").and_return(is_base_present).once()
    B.should_receive("pull").times(times_called)
    B.should_receive("check_container_creation").and_return(None).once()
    B.should_receive("get_image_id").and_return("1").once()
    B.should_receive("find_python_interpreter").and_return("").once()
    B.should_receive("create").once()
    B.should_receive("commit").once()
    B.should_receive("clean").once()

    A = flexmock(AnsibleRunner)
    A.should_receive('build').and_return("").once()

    application.build(build)

    build = application.db.get_build(build.build_id)
    assert not build.pulled == is_base_present

