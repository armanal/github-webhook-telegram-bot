import collections
import hashlib
import hmac
import logging
import json
import six


class Webhook(object):
    """
    Construct a webhook on the given :code:`app`.

    :param app: Flask app that will host the webhook
    :param endpoint: the endpoint for the registered URL rule
    :param secret: Optional secret, used to authenticate the hook comes from Github
    """

    def __init__(self, secret=None):
        self.secret = secret
        self._hooks = collections.defaultdict(list)
        self._logger = logging.getLogger("webhook")

    @property
    def secret(self):
        return self._secret

    @secret.setter
    def secret(self, secret):
        if secret is not None and not isinstance(secret, six.binary_type):
            secret = secret.encode("utf-8")
        self._secret = secret

    def hook(self, event_type="push"):
        """
        Registers a function as a hook. Multiple hooks can be registered for a given type, but the
        order in which they are invoke is unspecified.

        :param event_type: The event type this hook will be invoked for.
        """

        def decorator(func):
            self._hooks[event_type].append(func)
            return func

        return decorator

    def _get_digest(self, data):
        """Return message digest if a secret key was provided"""
        return hmac.new(self.secret, data, hashlib.sha256).hexdigest()

    def postreceive(self, request):
        """Callback from Flask"""

        digest = self._get_digest(request.data)

        if digest is not None:
            sig_parts = _get_header("x-hub-signature-256", request).split("=", 1)
            if not isinstance(digest, six.text_type):
                digest = six.text_type(digest)

            if (
                len(sig_parts) < 2
                or sig_parts[0] != "sha256"
                or not hmac.compare_digest(sig_parts[1], digest)
            ):
                return None

        event_type = _get_header("X-Github-Event", request)
        content_type = _get_header("content-type", request)
        data = (
            json.loads(request.form.to_dict(flat=True)["payload"])
            if content_type == "application/x-www-form-urlencoded"
            else request.get_json()
        )

        if data is None:
            return None

        self._logger.debug(f"event_type: {event_type}")
        self._logger.debug(f"content_type: {content_type}")
        self._logger.info(
            "%s (%s)",
            _format_event(event_type, data),
            _get_header("X-Github-Delivery", request),
        )
        self._logger.debug(f"Payload:\n {data}")

        # for hook in self._hooks.get(event_type, []):
        #     hook(data)

        return data, _format_event(event_type, data)


def _get_header(key, request):
    """Return message header"""

    try:
        return request.headers[key]
    except KeyError:
        return None


EVENT_DESCRIPTIONS = {
    "commit_comment": "{comment[user][login]} commented on "
    "{comment[commit_id]} in {repository[full_name]}",
    "create": "{sender[login]} created {ref_type} ({ref}) in "
    "{repository[full_name]}",
    "delete": "{sender[login]} deleted {ref_type} ({ref}) in "
    "{repository[full_name]}",
    "deployment": "{sender[login]} deployed {deployment[ref]} to "
    "{deployment[environment]} in {repository[full_name]}",
    "deployment_status": "deployment of {deployement[ref]} to "
    "{deployment[environment]} "
    "{deployment_status[state]} in "
    "{repository[full_name]}",
    "fork": "{forkee[owner][login]} forked {forkee[name]}",
    "gollum": "{sender[login]} edited wiki pages in {repository[full_name]}",
    "issue_comment": "{sender[login]} commented on issue #{issue[number]} "
    "in {repository[full_name]}",
    "issues": "{sender[login]} {action} issue #{issue[number]} in "
    "{repository[full_name]}",
    "member": "{sender[login]} {action} member {member[login]} in "
    "{repository[full_name]}",
    "membership": "{sender[login]} {action} member {member[login]} to team "
    "{team[name]} in {repository[full_name]}",
    "page_build": "{sender[login]} built pages in {repository[full_name]}",
    "ping": "ping from {sender[login]}",
    "public": "{sender[login]} publicized {repository[full_name]}",
    "pull_request": "{sender[login]} {action} pull #{pull_request[number]} in "
    "{repository[full_name]}",
    "pull_request_review": "{sender[login]} {action} {review[state]} "
    "review on pull #{pull_request[number]} in "
    "{repository[full_name]}",
    "pull_request_review_comment": "{comment[user][login]} {action} comment "
    "on pull #{pull_request[number]} in "
    "{repository[full_name]}",
    "release": "{release[author][login]} {action} {release[tag_name]} in "
    "{repository[full_name]}",
    "repository": "{sender[login]} {action} repository " "{repository[full_name]}",
    "status": "{sender[login]} set {sha} status to {state} in "
    "{repository[full_name]}",
    "team_add": "{sender[login]} added repository {repository[full_name]} to "
    "team {team[name]}",
    "watch": "{sender[login]} {action} watch in repository " "{repository[full_name]}",
}

FUNC_EVENT_FORMATS = {
    "push": lambda data: "[{data[head_commit][committer][name]}]({data[sender][html_url]}) \
pushed [{data[ref]}]({data[head_commit][url]}) in \
[{data[repository][full_name]}]({data[repository][html_url]})"
    + "\n\n".join(
        ["__commit message__: \n{commit[message]}" for commit in data["commits"]]
    ),
}


def _format_event(event_type, data):
    try:
        if event_type in EVENT_DESCRIPTIONS.keys():
            return EVENT_DESCRIPTIONS[event_type].format(**data)
        return FUNC_EVENT_FORMATS[event_type](data)
    except KeyError:
        return event_type


# -----------------------------------------------------------------------------
# Copyright 2015 Bloomberg Finance L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ----------------------------- END-OF-FILE -----------------------------------
