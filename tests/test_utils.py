# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from kent.utils import Item, parse_envelope


class Test_parse_envelope:
    def test_2_items(self):
        payload = (
            b'{"event_id":"9ec79c33ec9942ab8353589fcb2e04dc","dsn":"https://e12d836b15bb49d7bbf99e64295d995b:@sentry.io/42"}\n'
            b'{"type":"attachment","length":10,"content_type":"text/plain","filename":"hello.txt"}\n'
            b"\xef\xbb\xbfHello\r\n\n"
            b'{"type":"event","length":41,"content_type":"application/json","filename":"application.log"}\n'
            b'{"message":"hello world","level":"error"}\n'
        )

        items = list(parse_envelope(payload))

        assert items == [
            Item(
                envelope_header={
                    "dsn": "https://e12d836b15bb49d7bbf99e64295d995b:@sentry.io/42",
                    "event_id": "9ec79c33ec9942ab8353589fcb2e04dc",
                },
                header={
                    "content_type": "text/plain",
                    "filename": "hello.txt",
                    "length": 10,
                    "type": "attachment",
                },
                body=b"\xef\xbb\xbfHello\r\n",
            ),
            Item(
                envelope_header={
                    "dsn": "https://e12d836b15bb49d7bbf99e64295d995b:@sentry.io/42",
                    "event_id": "9ec79c33ec9942ab8353589fcb2e04dc",
                },
                header={
                    "content_type": "application/json",
                    "filename": "application.log",
                    "length": 41,
                    "type": "event",
                },
                body={
                    "level": "error",
                    "message": "hello world",
                },
            ),
        ]

    def test_2_items_missing_trailing_newline(self):
        payload = (
            b'{"event_id":"9ec79c33ec9942ab8353589fcb2e04dc","dsn":"https://e12d836b15bb49d7bbf99e64295d995b:@sentry.io/42"}\n'
            b'{"type":"attachment","length":10,"content_type":"text/plain","filename":"hello.txt"}\n'
            b"\xef\xbb\xbfHello\r\n\n"
            b'{"type":"event","length":41,"content_type":"application/json","filename":"application.log"}\n'
            b'{"message":"hello world","level":"error"}'
        )

        items = list(parse_envelope(payload))

        assert items == [
            Item(
                envelope_header={
                    "dsn": "https://e12d836b15bb49d7bbf99e64295d995b:@sentry.io/42",
                    "event_id": "9ec79c33ec9942ab8353589fcb2e04dc",
                },
                header={
                    "content_type": "text/plain",
                    "filename": "hello.txt",
                    "length": 10,
                    "type": "attachment",
                },
                body=b"\xef\xbb\xbfHello\r\n",
            ),
            Item(
                envelope_header={
                    "dsn": "https://e12d836b15bb49d7bbf99e64295d995b:@sentry.io/42",
                    "event_id": "9ec79c33ec9942ab8353589fcb2e04dc",
                },
                header={
                    "content_type": "application/json",
                    "filename": "application.log",
                    "length": 41,
                    "type": "event",
                },
                body={
                    "level": "error",
                    "message": "hello world",
                },
            ),
        ]

    def test_2_empty_attachments(self):
        payload = (
            b'{"event_id":"9ec79c33ec9942ab8353589fcb2e04dc"}\n'
            b'{"type":"attachment","length":0}\n'
            b"\n"
            b'{"type":"attachment","length":0}\n'
            b"\n"
        )

        items = list(parse_envelope(payload))

        assert items == [
            Item(
                envelope_header={
                    "event_id": "9ec79c33ec9942ab8353589fcb2e04dc",
                },
                header={
                    "length": 0,
                    "type": "attachment",
                },
                body=b"",
            ),
            Item(
                envelope_header={
                    "event_id": "9ec79c33ec9942ab8353589fcb2e04dc",
                },
                header={
                    "length": 0,
                    "type": "attachment",
                },
                body=b"",
            ),
        ]

    def test_2_empty_attachments_newline_omitted(self):
        payload = (
            b'{"event_id":"9ec79c33ec9942ab8353589fcb2e04dc"}\n'
            b'{"type":"attachment","length":0}\n'
            b"\n"
            b'{"type":"attachment","length":0}\n'
        )
        items = list(parse_envelope(payload))

        assert items == [
            Item(
                envelope_header={
                    "event_id": "9ec79c33ec9942ab8353589fcb2e04dc",
                },
                header={
                    "length": 0,
                    "type": "attachment",
                },
                body=b"",
            ),
            Item(
                envelope_header={
                    "event_id": "9ec79c33ec9942ab8353589fcb2e04dc",
                },
                header={
                    "length": 0,
                    "type": "attachment",
                },
                body=b"",
            ),
        ]

    def test_item_with_implicit_length(self):
        payload = (
            b'{"event_id":"9ec79c33ec9942ab8353589fcb2e04dc"}\n'
            b'{"type":"attachment"}\n'
            b"helloworld\n"
        )
        items = list(parse_envelope(payload))

        assert items == [
            Item(
                envelope_header={
                    "event_id": "9ec79c33ec9942ab8353589fcb2e04dc",
                },
                header={
                    "type": "attachment",
                },
                body=b"helloworld",
            ),
        ]

    def test_item_implicit_length_eof_terminator(self):
        payload = (
            b'{"event_id":"9ec79c33ec9942ab8353589fcb2e04dc"}\n'
            b'{"type":"attachment"}\n'
            b"helloworld"
        )
        items = list(parse_envelope(payload))

        assert items == [
            Item(
                envelope_header={
                    "event_id": "9ec79c33ec9942ab8353589fcb2e04dc",
                },
                header={
                    "type": "attachment",
                },
                body=b"helloworld",
            ),
        ]

    def test_empty_envelope_implicit_length_eof(self):
        payload = (
            b"{}\n"
            b'{"type":"session"}\n'
            b'{"started": "2020-02-07T14:16:00Z","attrs":{"release":"sentry-test@1.0.0"}}'
        )
        items = list(parse_envelope(payload))

        assert items == [
            Item(
                envelope_header={},
                header={
                    "type": "session",
                },
                body={
                    "attrs": {
                        "release": "sentry-test@1.0.0",
                    },
                    "started": "2020-02-07T14:16:00Z",
                },
            ),
        ]
