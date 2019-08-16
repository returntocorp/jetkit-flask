import json
from dataclasses import dataclass, astuple

import requests
from typing import Dict, Tuple, Optional
from flask import current_app, Flask

MAILGUN_BASE_URL = "https://api.mailgun.net/v3"


@dataclass
class Client:
    """
    Mailgun mail client.

    When instantiated without arguments, config is loaded from
    current Flask app using these fields:
        `MAILGUN_BASE_URL` (optional),
        `EMAIL_SENDING_ENABLED`,
        `SUPPORT_EMAIL`,
        `MAILGUN_API_KEY`,
        `MAILGUN_DEFAULT_SENDER` (optional)

    If `app` is provided, everything else is ignored and config is loaded from this app.
    """
    base_url: str = None
    enabled: bool = None
    support_email: str = None
    api_key: str = None
    default_sender: str = None
    app: Flask = None

    def __post_init__(self):
        if self.app is not None:
            self._load_config_from_app(self.app)
        elif self._none_of_the_fields_are_set():
            self._load_config_from_app(current_app)
        self._ensure_required_fields_are_set()

        self.base_url = self.base_url or MAILGUN_BASE_URL
        self.default_sender = self.default_sender or self.support_email

    def _none_of_the_fields_are_set(self) -> bool:
        self_fields = astuple(self)
        return all(field is None for field in self_fields)

    def _ensure_required_fields_are_set(self):
        required_fields = {
            "enabled": self.enabled,
            "support_email": self.support_email,
            "api_key": self.api_key,
        }
        for field, value in required_fields.items():
            if value is None:
                raise ValueError(
                    f"Can not instantiate {self.__class__} without '{field}' field"
                )

    def _load_config_from_app(self, app: Flask):
        self.base_url = app.config.get("MAILGUN_BASE_URL")
        self.enabled = app.config["EMAIL_SENDING_ENABLED"]
        self.support_email = app.config["SUPPORT_EMAIL"]
        self.api_key = app.config["MAILGUN_API_KEY"]
        self.default_sender = app.config.get("MAILGUN_DEFAULT_SENDER")

    def _auth(self) -> Tuple[str, str]:
        return "api", self.api_key

    def _send_message_url(self) -> str:
        return f"{self.base_url}/messages"

    def send_email_to(
        self,
        email: str,
        *,
        subject: str,
        body: str = None,
        sender: str = None,
        template: str = None,
        variables: Dict[str, str] = None,
    ) -> Optional[Dict]:
        variables = variables or {}

        if not self.enabled:
            return None

        if not sender:
            sender = self.default_sender

        # send message API request parameters
        params = {"from": sender, "to": email, "subject": subject}

        # template
        if template:
            params["template"] = template
            if variables and variables.keys:
                params["h:X-Mailgun-Variables"] = json.dumps(variables)
        elif not body:
            raise RuntimeError("template or body is required for sending email")
        else:
            # have body but not template
            params["text"] = body

        # do request
        res = requests.post(self._send_message_url(), auth=self._auth(), data=params)
        res.raise_for_status()
        return res.json()
