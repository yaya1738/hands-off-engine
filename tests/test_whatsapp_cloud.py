import json
import os
import unittest
from unittest.mock import patch

from messaging import whatsapp_cloud as wa


class WhatsAppCloudTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "WHATSAPP_ACCESS_TOKEN": "test-token",
            "WHATSAPP_PHONE_NUMBER_ID": "12345",
            "WHATSAPP_GRAPH_API_VERSION": "v24.0",
            "WHATSAPP_ALLOWED_RECIPIENTS": "+972547385735",
            "WHATSAPP_OPTED_IN_RECIPIENTS": "+972547385735",
        }, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_recipient_must_be_e164(self):
        with self.assertRaises(ValueError):
            wa.send_text("972547385735", "hello")

    def test_recipient_must_be_allowlisted(self):
        with self.assertRaises(wa.WhatsAppRecipientDenied):
            wa.send_text("+972501112222", "hello")

    def test_recipient_must_have_opted_in(self):
        os.environ["WHATSAPP_OPTED_IN_RECIPIENTS"] = ""
        with self.assertRaises(wa.WhatsAppRecipientDenied):
            wa.send_text("+972547385735", "hello")

    def test_configuration_is_fail_closed(self):
        del os.environ["WHATSAPP_ACCESS_TOKEN"]
        with self.assertRaises(wa.WhatsAppConfigurationError):
            wa.send_text("+972547385735", "hello")

    @patch("messaging.whatsapp_cloud.urllib.request.urlopen")
    def test_text_payload_and_auth_header(self, urlopen):
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return b'{"messages":[{"id":"wamid.test"}]}'
        urlopen.return_value = Response()

        result = wa.send_text("+972547385735", "Status update")
        self.assertEqual(result["messages"][0]["id"], "wamid.test")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")
        payload = json.loads(request.data)
        self.assertEqual(payload["to"], "+972547385735")
        self.assertEqual(payload["type"], "text")
        self.assertEqual(payload["text"]["body"], "Status update")

    @patch("messaging.whatsapp_cloud.urllib.request.urlopen")
    def test_template_payload(self, urlopen):
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return b'{"messages":[{"id":"wamid.template"}]}'
        urlopen.return_value = Response()
        wa.send_template("+972547385735", "project_update", "en_US")
        payload = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual(payload["type"], "template")
        self.assertEqual(payload["template"]["name"], "project_update")

    def test_rejects_invalid_template_name(self):
        with self.assertRaises(ValueError):
            wa.send_template("+972547385735", "Project Update!")

    @patch("messaging.whatsapp_cloud.urllib.request.urlopen")
    def test_api_failure_does_not_claim_success(self, urlopen):
        import urllib.error
        urlopen.side_effect = urllib.error.URLError("offline")
        with self.assertRaises(wa.WhatsAppDeliveryError):
            wa.send_text("+972547385735", "hello")


if __name__ == "__main__":
    unittest.main()
