import unittest
import os

os.environ["DEBUG"] = "false"

from app.core.languages import (
    detect_multilingual_language,
    get_all_languages,
    get_language_capability,
    LANGUAGE_REGISTRY,
)
from app.core.llm_client import llm_client


class MultilingualLanguageDetectionTests(unittest.TestCase):
    def test_english_query(self):
        lang = detect_multilingual_language("Hi, I want to know about your premium plan.", default_lang="en")
        self.assertEqual(lang, "en")

    def test_hinglish_query(self):
        lang = detect_multilingual_language("Accha iska monthly charge kitna hai?", default_lang="en")
        self.assertEqual(lang, "hinglish")

    def test_marathi_query(self):
        lang = detect_multilingual_language("He plan madhe appointment booking available aahe ka?", default_lang="en")
        self.assertEqual(lang, "mr")

    def test_devanagari_marathi_query(self):
        lang = detect_multilingual_language("हो, मला माहिती सांगा आणि नक्की वेळ सांगा.", default_lang="en")
        self.assertEqual(lang, "mr")

    def test_explicit_switch_to_english(self):
        lang = detect_multilingual_language("Okay, explain in English please.", default_lang="mr")
        self.assertEqual(lang, "en")

    def test_explicit_switch_to_marathi(self):
        lang = detect_multilingual_language("Please speak Marathi.", default_lang="en")
        self.assertEqual(lang, "mr")

    def test_spanish_worldwide_detection(self):
        lang = detect_multilingual_language("Hola, por favor cuanto cuesta el plan?", default_lang="en")
        self.assertEqual(lang, "es")


class LanguageRegistryTests(unittest.TestCase):
    def test_core_languages_are_supported(self):
        for code in ["en", "hi", "mr", "hinglish"]:
            cap = get_language_capability(code)
            self.assertIsNotNone(cap, f"Language {code} should be registered")
            self.assertEqual(cap.status, "supported")
            self.assertTrue(cap.stt)
            self.assertTrue(cap.tts)
            self.assertTrue(cap.llm)

    def test_experimental_languages_do_not_fake_stt_tts(self):
        cap = get_language_capability("unknown_dialect")
        self.assertIsNotNone(cap)
        self.assertFalse(cap.stt)
        self.assertFalse(cap.tts)
        self.assertTrue(cap.llm)
        self.assertEqual(cap.status, "experimental")

    def test_get_all_languages_returns_registry_list(self):
        langs = get_all_languages()
        self.assertGreaterEqual(len(langs), 20)
        codes = [l["code"] for l in langs]
        self.assertIn("en", codes)
        self.assertIn("es", codes)
        self.assertIn("mr", codes)


class AgentGreetingAndBargeInTests(unittest.TestCase):
    def test_agent_speaks_first_on_call_start(self):
        greeting = llm_client._rule_fallback("[CALL_START] Greet the caller now.")
        self.assertIn("Hi, I'm", greeting)
        self.assertIn("AI assistant", greeting)
        self.assertIn("How can I help you today?", greeting)

    def test_barge_in_instant_pricing_reply(self):
        reply = llm_client._rule_fallback("Wait, stop. Just tell me the price.")
        self.assertIn("999", reply)
        self.assertIn(":::TOOL_CALL:::", reply)
        self.assertIn("get_offering_price", reply)

    def test_barge_in_stop_reply(self):
        reply = llm_client._rule_fallback("Stop")
        self.assertIn("stopped", reply.lower())


if __name__ == "__main__":
    unittest.main()
