#
# Copyright (c) 2021 Nightwatch Cybersecurity.
#
# This file is part of icetrust
# (see https://github.com/nightwatchcybersecurity/icetrust).
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
import os, re, shutil
import tempfile

import gnupg, pytest

from icetrust.utils import DEFAULT_HASH_ALGORITHM, IcetrustUtils, MsgCallback

# Directory with test data
TEST_DIR = 'test_data'
FILE1_HASH = '07fe4d4a25718241af145a93f890eb5469052e251d199d173bd3bd50c3bb4da2'
FILE2_HASH = 'c6de01eef7b93f5112af99a8754c50fdade4aaa6c85d4ab3fbf9b24d41e0d875'


@pytest.fixture
def copy_keyring(tmp_path):
    # Copying keyring to speed things up
    shutil.copy(os.path.join(TEST_DIR, 'pubring.kbx'), tmp_path)


@pytest.fixture
def mock_msg_callback():
    # Return mock message callback object
    return MsgCallback()


# Tests for misc utils methods
class TestUtils(object):
    def test_const_default_algorithm(self):
        assert DEFAULT_HASH_ALGORITHM == 'sha256'

    def test_get_version_format_valid(self):
        pattern = re.compile(r'^(\d+\.)?(\d+\.)?(\*|\d+)$')
        assert pattern.match(IcetrustUtils.get_version()) is not None

    def test_process_verbose_flag_valid(self):
        assert IcetrustUtils.process_verbose_flag(False) is False
        assert IcetrustUtils.process_verbose_flag(None) is False

    def test_MsgCallback(self):
        msg_callback = MsgCallback()
        msg_callback.echo('test1')
        msg_callback.echo('test2')
        assert len(msg_callback.messages) == 2
        assert msg_callback.messages[0] == 'test1'
        assert msg_callback.messages[1] == 'test2'


# Tests for utils.compare_files()
class TestUtilsCompareFiles(object):
    def test_doesnt_exists_file1(self):
        assert IcetrustUtils.compare_files(os.path.join(TEST_DIR, 'foobar.txt'),
                                           os.path.join(TEST_DIR, 'file1.txt')) is False

    def test_doesnt_exists_file1_verbose(self, mock_msg_callback):
        assert IcetrustUtils.compare_files(os.path.join(TEST_DIR, 'foobar.txt'),
                                           os.path.join(TEST_DIR, 'file1.txt'),
                                           msg_callback=mock_msg_callback) is False
        assert len(mock_msg_callback.messages) == 1
        assert mock_msg_callback.messages[0] == "[Errno 2] No such file or directory: 'test_data/foobar.txt'"

    def test_doesnt_exists_file2(self):
        assert IcetrustUtils.compare_files(os.path.join(TEST_DIR, 'file1.txt'),
                                           os.path.join(TEST_DIR, 'file2.txt')) is False

    def test_doesnt_exists_all_files(self):
        assert IcetrustUtils.compare_files(os.path.join(TEST_DIR, 'foobar1.txt'),
                                           os.path.join(TEST_DIR, 'foobar2.txt')) is False

    def test_valid(self):
        cmd_output = []
        assert IcetrustUtils.compare_files(os.path.join(TEST_DIR, 'file1.txt'),
                                           os.path.join(TEST_DIR, 'file1.txt'), cmd_output=cmd_output) is True
        assert len(cmd_output) == 0

    def test_valid_verbose(self, mock_msg_callback):
        assert IcetrustUtils.compare_files(os.path.join(TEST_DIR, 'file1.txt'),
                                           os.path.join(TEST_DIR, 'file1.txt'),
                                           msg_callback=mock_msg_callback) is True
        assert len(mock_msg_callback.messages) == 2
        assert mock_msg_callback.messages[0] == 'File1 checksum: ' + FILE1_HASH
        assert mock_msg_callback.messages[1] == 'File2 checksum: ' + FILE1_HASH

    def test_invalid1(self):
        assert IcetrustUtils.compare_files(os.path.join(TEST_DIR, 'file1.txt'),
                                           os.path.join(TEST_DIR, 'file2.txt')) is False

    def test_invalid1_verbose(self, mock_msg_callback):
        cmd_output = []
        assert IcetrustUtils.compare_files(os.path.join(TEST_DIR, 'file1.txt'),
                                           os.path.join(TEST_DIR, 'file2.txt'),
                                           msg_callback=mock_msg_callback) is False
        assert len(mock_msg_callback.messages) == 2
        assert mock_msg_callback.messages[0] == 'File1 checksum: ' + FILE1_HASH
        assert mock_msg_callback.messages[1] == 'File2 checksum: ' + FILE2_HASH

    def test_invalid2(self):
        assert IcetrustUtils.compare_files(os.path.join(TEST_DIR, 'file2.txt'),
                                           os.path.join(TEST_DIR, 'file1.txt')) is False

    def test_invalid3_cmd_output(self):
        cmd_output = []
        assert IcetrustUtils.compare_files(os.path.join(TEST_DIR, 'file2.txt'),
                                           os.path.join(TEST_DIR, 'file1.txt'), cmd_output=cmd_output) is False
        assert len(cmd_output) == 2
        assert cmd_output[0] == 'File1 checksum: ' + FILE2_HASH
        assert cmd_output[1] == 'File2 checksum: ' + FILE1_HASH


# Tests for utils.pgp_import_keys()
class TestUtilsPgpImportKeys(object):
    @pytest.mark.slow
    def test_valid_fromfile(self, tmp_path):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        assert IcetrustUtils.pgp_import_keys(gpg, keyfile=os.path.join(TEST_DIR, 'pgp_keys.txt')) is True

    @pytest.mark.slow
    def test_valid_fromfile_verbose(self, tmp_path, mock_msg_callback):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        assert IcetrustUtils.pgp_import_keys(gpg, keyfile=os.path.join(TEST_DIR, 'pgp_keys.txt'),
                                             msg_callback=mock_msg_callback) is True
        assert len(mock_msg_callback.messages) == 2
        assert mock_msg_callback.messages[0] == '--- Results of key import ---\n'
        assert '[GNUPG:] IMPORTED FBFCC82A015E7330' in mock_msg_callback.messages[1]

    @pytest.mark.network
    def test_valid_fromkeyid(self, mock_msg_callback):
        # TODO: Switch to use tmp_path fixture
        temp_dir_obj = tempfile.TemporaryDirectory()
        tmp_path = os.path.join(temp_dir_obj.name, '')
        gpg = IcetrustUtils.pgp_init(tmp_path)
        assert IcetrustUtils.pgp_import_keys(gpg, keyid='C8EF5FF3BF864E50', keyserver='keyserver.ubuntu.com',
                                             msg_callback=mock_msg_callback) is True

    @pytest.mark.network
    def test_invalid_fromkeyid(self, mock_msg_callback):
        # TODO: Switch to use tmp_path fixture
        temp_dir_obj = tempfile.TemporaryDirectory()
        tmp_path = os.path.join(temp_dir_obj.name, '')
        gpg = IcetrustUtils.pgp_init(tmp_path)
        assert IcetrustUtils.pgp_import_keys(gpg, keyid='foobar', keyserver='keyserver.ubuntu.com',
                                             msg_callback=mock_msg_callback) is False

    def test_invalid_file(self, tmp_path):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        assert IcetrustUtils.pgp_import_keys(gpg, keyfile='foobar') is False

    def test_invalid_file_verbose(self, tmp_path, mock_msg_callback):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        assert IcetrustUtils.pgp_import_keys(gpg, keyfile='foobar', msg_callback=mock_msg_callback) is False
        assert len(mock_msg_callback.messages) == 1
        assert mock_msg_callback.messages[0] == "[Errno 2] No such file or directory: 'foobar'"

    def test_invalid_file_no_keys(self, tmp_path):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        assert IcetrustUtils.pgp_import_keys(gpg, keyfile=os.path.join(TEST_DIR, 'file1.txt.sig')) is False

    def test_invalid_missing_arguments1(self, tmp_path):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        with pytest.raises(ValueError):
            IcetrustUtils.pgp_import_keys(gpg)

    def test_invalid_missing_arguments2(self, tmp_path):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        with pytest.raises(ValueError):
            IcetrustUtils.pgp_import_keys(gpg, keyid='foobar')

    def test_invalid_missing_arguments3(self, tmp_path):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        with pytest.raises(ValueError):
            IcetrustUtils.pgp_import_keys(gpg, keyserver='foobar')


# Tests for utils.pgp_import_keys()
class TestUtilsPgpVerify(object):
    def test_invalid_file_doesnt_exist(self, tmp_path, copy_keyring):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        assert IcetrustUtils.pgp_verify(gpg, os.path.join(TEST_DIR, 'foobar'),
                                        os.path.join(TEST_DIR, 'file1.txt.sig')) is False

    def test_invalid_signaturefile_doesnt_exist(self, tmp_path, copy_keyring):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        assert IcetrustUtils.pgp_verify(gpg, os.path.join(TEST_DIR, 'file1.txt'),
                                        os.path.join(TEST_DIR, 'foobar.sig')) is False

    def test_invalid_wrong_file(self, tmp_path, copy_keyring):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        assert IcetrustUtils.pgp_verify(gpg, os.path.join(TEST_DIR, 'file2.txt'),
                                        os.path.join(TEST_DIR, 'file1.txt.sig')) is False

    def test_invalid_wrong_signature(self, tmp_path, copy_keyring):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        assert IcetrustUtils.pgp_verify(gpg, os.path.join(TEST_DIR, 'file1.txt'),
                                        os.path.join(TEST_DIR, 'file1.SHA256SUMS.txt.sig')) is False

    def test_invalid_wrong_signature_verbose(self, tmp_path, copy_keyring, mock_msg_callback):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        assert IcetrustUtils.pgp_verify(gpg, os.path.join(TEST_DIR, 'file1.txt'),
                                        os.path.join(TEST_DIR, 'file1.SHA256SUMS.txt.sig'),
                                        msg_callback=mock_msg_callback) is False
        assert len(mock_msg_callback.messages) == 1
        assert mock_msg_callback.messages[0] ==\
               "[Errno 2] No such file or directory: 'test_data/file1.SHA256SUMS.txt.sig'"

    def test_invalid_invalid_signature(self, tmp_path, copy_keyring):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        assert IcetrustUtils.pgp_verify(gpg, os.path.join(TEST_DIR, 'file1.txt'),
                                        os.path.join(TEST_DIR, 'file2.txt')) is False

    def test_valid_file(self, tmp_path, copy_keyring):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        assert IcetrustUtils.pgp_verify(gpg, os.path.join(TEST_DIR, 'file1.txt'),
                                        os.path.join(TEST_DIR, 'file1.txt.sig')) is True

    def test_valid_file_verbose(self, tmp_path, copy_keyring, mock_msg_callback):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        assert IcetrustUtils.pgp_verify(gpg, os.path.join(TEST_DIR, 'file1.txt'),
                                        os.path.join(TEST_DIR, 'file1.txt.sig'),
                                        msg_callback=mock_msg_callback) is True
        assert len(mock_msg_callback.messages) == 2
        assert mock_msg_callback.messages[0] == '\n--- Results of verification ---'
        assert '[GNUPG:] SIG_ID crXxiKwsoGFwp1pyl+csVQd53aA 2021-04-22 1619099716' in mock_msg_callback.messages[1]

    def test_valid_checksums(self, tmp_path, copy_keyring):
        gpg = IcetrustUtils.pgp_init(tmp_path)
        assert IcetrustUtils.pgp_verify(gpg, os.path.join(TEST_DIR, 'file1.txt.SHA256SUMS'),
                                        os.path.join(TEST_DIR, 'file1.txt.SHA256SUMS.sig')) is True


# Tests for utils.pgp_init()
class TestUtilsPgpInit(object):
    def test_invalid_bad_dir(self):
        with pytest.raises(ValueError):
            IcetrustUtils.pgp_init("foobar")

    def test_valid(self):
        assert type(IcetrustUtils.pgp_init()) is gnupg.GPG

    def test_valid_with_dir(self, tmp_path):
        new_dir = os.path.join(tmp_path, "sub")
        os.mkdir(new_dir)
        assert type(IcetrustUtils.pgp_init(gpg_home_dir=new_dir)) is gnupg.GPG


# Tests for utils.verify_checksum()
class TestUtilsVerifyChecksum(object):
    def test_doesnt_exists_file(self):
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'foobar.txt'), DEFAULT_HASH_ALGORITHM,
                                             checksumfile=os.path.join(TEST_DIR, 'file1.txt.SHA256SUMS')) is False

    def test_doesnt_exists_file_verbose(self, mock_msg_callback):
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'foobar.txt'), DEFAULT_HASH_ALGORITHM,
                                             checksumfile=os.path.join(TEST_DIR, 'file1.txt.SHA256SUMS'),
                                             msg_callback=mock_msg_callback) is False
        assert len(mock_msg_callback.messages) == 1
        assert mock_msg_callback.messages[0] == "[Errno 2] No such file or directory: 'test_data/foobar.txt'"

    def test_doesnt_exists_checksum_file(self):
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt'), DEFAULT_HASH_ALGORITHM,
                                             checksumfile=os.path.join(TEST_DIR, 'foobar.txt')) is False

    def test_doesnt_exists_checksum_file_valid(self, mock_msg_callback):
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt'), DEFAULT_HASH_ALGORITHM,
                                             checksumfile=os.path.join(TEST_DIR, 'foobar.txt'),
                                             msg_callback=mock_msg_callback) is False
        assert len(mock_msg_callback.messages) == 3
        assert mock_msg_callback.messages[0] == 'Algorithm: sha256'
        assert mock_msg_callback.messages[1] == 'File hash: ' + FILE1_HASH
        assert mock_msg_callback.messages[2] == "[Errno 2] No such file or directory: 'test_data/foobar.txt'"

    def test_valid_checksumfile(self):
        cmd_output = []
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt'), DEFAULT_HASH_ALGORITHM,
                                             checksumfile=os.path.join(TEST_DIR, 'file1.txt.SHA256SUMS'),
                                             cmd_output=cmd_output) is True
        assert len(cmd_output) == 0

    def test_valid_checksum(self):
        cmd_output = []
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt'), DEFAULT_HASH_ALGORITHM,
                                             checksum_value=FILE1_HASH,
                                             cmd_output=cmd_output) is True
        assert len(cmd_output) == 0

    def test_valid_checksum_verbose(self, mock_msg_callback):
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt'), DEFAULT_HASH_ALGORITHM,
                                             checksum_value=FILE1_HASH,
                                             msg_callback=mock_msg_callback) is True
        assert len(mock_msg_callback.messages) == 2
        assert mock_msg_callback.messages[0] == 'Algorithm: sha256'
        assert mock_msg_callback.messages[1] == 'File hash: ' + FILE1_HASH

    def test_valid_checksum_and_invalid_file(self):
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt'), DEFAULT_HASH_ALGORITHM,
                                             checksum_value=FILE1_HASH,
                                             checksumfile=os.path.join(TEST_DIR, 'foobar.txt')) is True

    def test_valid_checksum_uppercase(self):
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt'), DEFAULT_HASH_ALGORITHM,
                                             checksum_value=FILE1_HASH.upper()) is True

    def test_valid_checksum_whitespace(self):
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt'), DEFAULT_HASH_ALGORITHM,
                                             checksum_value=' ' + FILE1_HASH + ' ') is True

    def test_invalid1_checksum(self):
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt.SHA256SUMS'), DEFAULT_HASH_ALGORITHM,
                                             checksum_value='foobar') is False

    def test_invalid1_checksum_with_cmd_output(self):
        cmd_output = []
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt.SHA256SUMS'), DEFAULT_HASH_ALGORITHM,
                                             checksum_value='foobar', cmd_output=cmd_output) is False
        assert len(cmd_output) == 3
        assert cmd_output[0] == 'Algorithm: sha256'
        assert cmd_output[1] == 'File checksum: ca68d23d93b2611b380a57fa076684e1f5fa76d0d6bbd6df00c9aed28347e383'
        assert cmd_output[2] == 'Checksum to check against: foobar'

    def test_invalid1_checksumfile(self):
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt.SHA256SUMS'), DEFAULT_HASH_ALGORITHM,
                                             checksumfile=os.path.join(TEST_DIR, 'file1.txt')) is False

    def test_invalid1_checksumfile_with_cmd_output(self):
        cmd_output = []
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt.SHA256SUMS'), DEFAULT_HASH_ALGORITHM,
                                             checksumfile=os.path.join(TEST_DIR, 'file1.txt'),
                                             cmd_output=cmd_output) is False
        assert len(cmd_output) == 3
        assert cmd_output[0] == 'Algorithm: sha256'
        assert cmd_output[1] == 'File checksum: ca68d23d93b2611b380a57fa076684e1f5fa76d0d6bbd6df00c9aed28347e383'
        assert cmd_output[2] == 'No match found in checksum file'

    def test_invalid2_checksumfile(self):
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file2.txt'), DEFAULT_HASH_ALGORITHM,
                                             checksumfile=os.path.join(TEST_DIR, 'file1.txt.SHA256SUMS')) is False

    def test_invalid_algorithm_checksum1(self):
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt'), 'md5',
                                             checksum_value=FILE1_HASH) is False

    def test_invalid_algorithm_checksum2(self):
        with pytest.raises(ValueError):
            IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt'), 'rc4', checksum_value=FILE1_HASH)

    def test_invalid_algorithm_checksumfile1(self):
        assert IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt'), 'md5',
                                             checksumfile=os.path.join(TEST_DIR, 'file1.txt.SHA256SUMS')) is False

    def test_invalid_algorithm_checksumfile2(self):
        with pytest.raises(ValueError):
            IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt'), 'rc4',
                                          checksumfile=os.path.join(TEST_DIR, 'file1.txt.SHA256SUMS'))

    def test_invalid_missing_arguments1(self):
        with pytest.raises(ValueError):
            IcetrustUtils.verify_checksum(os.path.join(TEST_DIR, 'file1.txt'), DEFAULT_HASH_ALGORITHM)
