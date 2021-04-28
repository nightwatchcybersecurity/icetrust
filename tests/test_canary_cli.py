#
# Copyright (c) 2021 Nightwatch Cybersecurity.
#
# This file is part of icecrust
# (see https://github.com/nightwatchcybersecurity/icecrust).
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
import json

from click.testing import CliRunner
import jsonschema, pytest

from icecrust.canary_cli import cli
from icecrust.utils import IcecrustUtils
from icecrust.canary_utils import CANARY_INPUT_SCHEMA, CANARY_OUTPUT_SCHEMA

from test_utils import TEST_DIR, FILE1_HASH, FILE2_HASH


# Tests for CLI class
class TestCanary(object):
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert result.output == 'icecrust_canary, version ' + IcecrustUtils.get_version() + '\n'


# Tests for "verify" command()
class TestCanaryVerify(object):
    @pytest.mark.network
    def test_compare_invalid(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(cli, ['verify', TEST_DIR + 'canary/compare_pnpm_input.json'])
        assert result.exit_code == -1
        assert result.output == 'Using verification mode: COMPARE_FILES\n' + \
               'Downloading file: https://get.pnpm.io/v6.js\n' + \
               'ERROR: File cannot be verified!\n'

    @pytest.mark.network
    def test_checksum_valid(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(cli, ['verify', TEST_DIR + 'canary/checksum_pnpm_input.json'])
        assert result.exit_code == 0
        assert result.output == 'Using verification mode: VERIFY_VIA_CHECKSUM\n' + \
               'Downloading file: https://get.pnpm.io/v6.js\n' + \
               'File verified\n'

    @pytest.mark.network
    def test_checksumfile_valid(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(cli, ['verify', TEST_DIR + 'canary/checksumfile_pnpm_input.json'])
        assert result.exit_code == 0
        assert result.output == 'Using verification mode: VERIFY_VIA_CHECKSUMFILE\n' + \
               'Downloading file: https://get.pnpm.io/v6.js\n' + \
               'File verified\n'

    @pytest.mark.network
    def test_pgp_valid(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(cli, ['verify', TEST_DIR + 'canary/pgp_pnpm_input.json'])
        assert result.exit_code == 0
        assert result.output == 'Using verification mode: VERIFY_VIA_PGP\n' + \
               'Downloading file: https://get.pnpm.io/SHASUMS256.txt\n' + \
               'File verified\n'

    @pytest.mark.network
    def test_pgpchecksumfile_valid(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(cli, ['verify', TEST_DIR + 'canary/pgpchecksumfile_pnpm_input.json'])
        assert result.exit_code == 0
        assert result.output == 'Using verification mode: VERIFY_VIA_PGPCHECKSUMFILE\n' + \
               'Downloading file: https://get.pnpm.io/v6.js\n' + \
               'File verified\n'
