from jb.mail.base import MailClientBase
from jb.mail.constant import MailerImplementation
import requests
import pytest
from unittest.mock import patch


@pytest.fixture
def dummy_client():
    yield MailClientBase.new_for_impl(
        impl=MailerImplementation.dummy,
        from_flask=False,
        enabled=True,
        support_email="test@test.com",
    )


@pytest.fixture
def mailgun_client():
    yield MailClientBase.new_for_impl(
        impl=MailerImplementation.mailgun, from_flask=True
    )


@pytest.fixture
def mocked_requests(mocker):
    mocker.patch.object(requests, "post", autospec=True)


def test_login(app, mocked_requests, mailgun_client):
    test_email = "test@test.com"
    mailgun_client.send(
        to=[test_email], subject="mail test client", body="automated test"
    )


def test_dummy_mailer(dummy_client):
    with patch.object(dummy_client, "send") as send_patch:
        dummy_client.send()
        send_patch.assert_called_once()
