from pathlib import Path
from deluge_control.sftp import get_sftp_connection


def test_ls():
    """
    A user can sftp into remote and detect an added test file
    """
    test_dir = "deluge_control_tests"
    test_file = "test_sftp.txt"

    with get_sftp_connection() as sftp:

        # Setup
        try:
            sftp.mkdir(test_dir)
            assert not test_file in sftp.listdir("deluge_control_tests")
        except:
            sftp.walktree(
                test_dir,
                lambda file: sftp.remove(file),
                lambda dir: sftp.rmdir(dir),
                lambda: None,
                recurse=True,
            )
            sftp.rmdir(test_dir)
            raise
        else:
            try:
                with sftp.cd(test_dir):
                    sftp.put(f"{str(Path(__file__).parent)}/data/test_sftp.txt")
            except:
                sftp.rmdir(test_dir)

        with get_sftp_connection():
            try:
                assert test_file in (sftp.listdir(test_dir))
            finally:
                sftp.remove(f"{test_dir}/{test_file}")
