# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.

import jwt
from default import Test, with_context
from pybossa.auth import jwt_authorize_project
from pybossa.auth.errcodes import *
from factories import ProjectFactory
from mock import patch


class TestAuthentication(Test):

    def test_api_authenticate(self):
        """Test AUTHENTICATION works"""
        self.create()
        res = self.app.get('/?api_key=%s' % self.api_key)
        assert '<a href="/account/signout"' in res.data, res.data
        assert 'checkpoint::logged-in::tester' in res.data, res.data


def handle_error(error):
    return error


class TestJwtAuthorization(Test):


    @patch('pybossa.auth.handle_error')
    def test_jwt_authorize_project_no_payload(self, mymock):
        """Test JWT no payload."""
        mymock.side_effect = handle_error
        project = ProjectFactory.create()
        res = jwt_authorize_project(project, None)
        assert res == INVALID_HEADER_MISSING, res

    @patch('pybossa.auth.handle_error')
    def test_jwt_authorize_project_no_bearer(self, mymock):
        """Test JWT no bearer."""
        mymock.side_effect = handle_error
        project = ProjectFactory.create()
        bearer = 'Something %s' % project.secret_key
        res = jwt_authorize_project(project, bearer)
        assert res == INVALID_HEADER_BEARER, res

    @patch('pybossa.auth.handle_error')
    def test_jwt_authorize_project_bearer_no_token(self, mymock):
        """Test JWT bearer and no token."""
        mymock.side_effect = handle_error
        project = ProjectFactory.create()
        bearer = 'Bearer '
        res = jwt_authorize_project(project, bearer)
        assert res == INVALID_HEADER_TOKEN, res

    @patch('pybossa.auth.handle_error')
    def test_jwt_authorize_project_bearer_token(self, mymock):
        """Test JWT bearer token and something else."""
        mymock.side_effect = handle_error
        project = ProjectFactory.create()
        bearer = 'Bearer %s algo' % project.secret_key
        res = jwt_authorize_project(project, bearer)
        assert res == INVALID_HEADER_BEARER_TOKEN, res

    @patch('pybossa.auth.jwt.decode')
    @patch('pybossa.auth.handle_error')
    def test_jwt_authorize_project_wrong_project(self, mymock, mydecode):
        """Test JWT wrong decoded project."""
        mymock.side_effect = handle_error
        mydecode.return_value = dict(project_id=99999, short_name='something')
        project = ProjectFactory.create()
        bearer = 'Bearer %s' % project.secret_key
        res = jwt_authorize_project(project, bearer)
        assert res == WRONG_PROJECT_SIGNATURE, res

    @patch('pybossa.auth.handle_error')
    def test_jwt_authorize_project_decode_error(self, mymock):
        """Test JWT decode error."""
        mymock.side_effect = handle_error
        project = ProjectFactory.create()
        bearer = 'Bearer %s%s' % (project.secret_key, "a")
        res = jwt_authorize_project(project, bearer)
        assert res == DECODE_ERROR_SIGNATURE, res

    @patch('pybossa.auth.handle_error')
    def test_jwt_authorize(self, mymock):
        """Test JWT decode works."""
        project = ProjectFactory.create()
        token = jwt.encode({'short_name': project.short_name,
                            'project_id': project.id},
                            project.secret_key, algorithm='HS256')
        mymock.side_effect = handle_error
        bearer = 'Bearer %s' % (token)
        res = jwt_authorize_project(project, bearer)
        assert res is True, res
