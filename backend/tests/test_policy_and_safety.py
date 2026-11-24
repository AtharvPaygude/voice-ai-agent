import unittest
import os

os.environ["DEBUG"] = "false"

from app.api.routes.config import AgentConfig
from app.api.routes.tools import _confirmation_required, _tool_allowed
from app.api.websocket import _classify_healthcare_request


class ToolPolicyTests(unittest.TestCase):
    def test_tool_aliases_are_allowed_by_canonical_profile_tool(self):
        self.assertTrue(_tool_allowed("book_appointment", ["book_slot"]))
        self.assertTrue(_tool_allowed("get_product_price", ["get_offering_price"]))

    def test_disabled_tool_is_not_allowed(self):
        self.assertFalse(_tool_allowed("send_sms", ["book_slot", "transfer_to_human"]))

    def test_confirmation_response_is_clear(self):
        response = _confirmation_required("cancel_slot", "cancellation")

        self.assertEqual(response.status, "requires_confirmation")
        self.assertEqual(response.result["required_confirmation"], "cancellation")
        self.assertIn("confirm", response.message.lower())


class HealthcareSafetyTests(unittest.TestCase):
    def test_medical_advice_request_is_flagged(self):
        self.assertEqual(
            _classify_healthcare_request("What medicine dosage should I take for these symptoms?"),
            "medical_advice",
        )

    def test_emergency_request_is_flagged(self):
        self.assertEqual(
            _classify_healthcare_request("I have chest pain and cannot breathe"),
            "emergency",
        )

    def test_admin_clinic_workflow_is_allowed(self):
        self.assertIsNone(_classify_healthcare_request("Can I book an appointment tomorrow?"))
        self.assertIsNone(_classify_healthcare_request("What are your clinic timings and location?"))


class ConfigValidationTests(unittest.TestCase):
    def test_agent_config_keeps_language_switch_defaults(self):
        config = AgentConfig()

        self.assertEqual(config.confidence_threshold, 0.7)
        self.assertEqual(config.stability_count, 2)
        self.assertIn("hinglish", config.supported_languages)


if __name__ == "__main__":
    unittest.main()
