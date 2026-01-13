from xrayradar.models import _get_frame_info


def test_get_frame_info_uses_patched_getattribute_branch(tmp_path):
    p = tmp_path / "x.py"
    p.write_text("a = 1\nraise RuntimeError('x')\n")

    class DummyCode:
        co_filename = str(p)
        co_name = "f"

    class DummyFrame:
        def __init__(self):
            self.__dict__[
                "__getattribute__"] = lambda name: DummyCode if name == "f_code" else 2

        # If the code accidentally uses normal attribute access, crash.
        @property
        def f_code(self):
            raise AssertionError("should use patched __getattribute__")

        @property
        def f_lineno(self):
            raise AssertionError("should use patched __getattribute__")

    frame = DummyFrame()
    info = _get_frame_info(frame)

    assert info is not None
    assert info.filename == str(p)
    assert info.lineno == 2
