import json
import unittest
from dataclasses import replace
from types import SimpleNamespace

from app.config import normalize_foundry_base_url, settings
from app.models.schemas import ChatMessage, ChatRequest
from app.services import ai_service, chat_pipeline, prompts, scheme_store
from app.services.providers.azure_foundry import AzureFoundryProvider, ProviderError
from app.services.providers.base import ChatContext
from app.services.providers.local import LocalProvider, compose_answer, detect_intent


# ----------------------------------------------------------------- fakes
class FakeBadRequest(Exception):
    status_code = 400


class FakeServerError(Exception):
    status_code = 500


def completion(text, model="fake-model"):
    return SimpleNamespace(model=model, choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


def chunk(text=None, finish=None, empty=False):
    if empty:
        return SimpleNamespace(choices=[])
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text), finish_reason=finish)])


class FakeCompletions:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def fake_client(*responses):
    completions = FakeCompletions(*responses)
    return SimpleNamespace(chat=SimpleNamespace(completions=completions)), completions


def azure_settings(**over):
    base = dict(
        ai_provider="azure",
        azure_endpoint="https://demo.openai.azure.com/",
        azure_api_key="test-key",
        azure_deployment="jansaathi-gpt",
    )
    base.update(over)
    return replace(settings, **base)


def make_ctx(message="pension for my father", language="en", history=None):
    payload = ChatRequest(message=message, language=language, history=history or [])
    return chat_pipeline.prepare(payload)


# ----------------------------------------------------------------- config
class TestConfig(unittest.TestCase):
    def test_normalize_endpoint_variants(self):
        want = "https://demo.openai.azure.com/openai/v1/"
        for raw in [
            "https://demo.openai.azure.com",
            "https://demo.openai.azure.com/",
            "https://demo.openai.azure.com/openai/v1/",
            "demo.openai.azure.com",
        ]:
            self.assertEqual(normalize_foundry_base_url(raw), want, raw)
        self.assertEqual(
            normalize_foundry_base_url("https://demo.services.ai.azure.com/api/projects/my-project"),
            "https://demo.services.ai.azure.com/openai/v1/",
        )
        self.assertEqual(normalize_foundry_base_url(""), "")

    def test_effective_provider(self):
        self.assertEqual(azure_settings().effective_provider, "azure")
        self.assertEqual(azure_settings(azure_deployment="").effective_provider, "local")   # misconfigured -> local
        self.assertEqual(azure_settings(ai_provider="local").effective_provider, "local")
        self.assertEqual(azure_settings(azure_api_key="").azure_auth_mode, "entra_id")
        self.assertEqual(azure_settings().azure_auth_mode, "api_key")


# ----------------------------------------------------------------- pipeline + prompt
class TestPipeline(unittest.TestCase):
    def test_prepare_redacts_and_retrieves(self):
        ctx = make_ctx("pension for my father, my number is 98765 43210")
        self.assertTrue(ctx.redacted)
        self.assertNotIn("98765", ctx.message)
        self.assertEqual(ctx.schemes[0].id, "old-age-pension")
        self.assertNotIn("98765", json.dumps(ctx.messages))            # never reaches the model
        self.assertIn("private number", ctx.messages[0]["content"])   # model is told to remind the user

    def test_prompt_is_grounded_and_localised(self):
        ctx = make_ctx("ਪੈਨਸ਼ਨ ਚਾਹੀਦੀ ਹੈ", language="pa")
        system = ctx.messages[0]["content"]
        self.assertIn("Punjabi", system)
        self.assertIn("ਪੈਨਸ਼ਨ", system)                                # scheme record in the user's language
        self.assertIn("Old Age Pension Scheme", system)                # English name for disambiguation
        self.assertIn("Never invent", system)
        self.assertEqual(ctx.messages[-1], {"role": "user", "content": "ਪੈਨਸ਼ਨ ਚਾਹੀਦੀ ਹੈ"})

    def test_prompt_without_match_says_so(self):
        system = prompts.build_system_prompt("en", [])
        self.assertIn("no scheme record matched", system)

    def test_history_is_trimmed(self):
        hist = [ChatMessage(role="user", content=f"q{i}") for i in range(30)]
        ctx = make_ctx("hi", history=hist)
        self.assertEqual(len(ctx.history), settings.max_history_messages)

    def test_suggestions(self):
        matched = scheme_store.load_schemes()[:1]
        self.assertEqual(chat_pipeline.suggestions_for(matched, "en")[0], "Who can apply?")
        self.assertEqual(len(chat_pipeline.suggestions_for([], "pa")), 3)
        self.assertEqual(chat_pipeline.suggestions_for(matched, "xx")[0], "Who can apply?")   # unknown language -> English


# ----------------------------------------------------------------- local provider
class TestLocalProvider(unittest.TestCase):
    def test_answer_in_each_language_uses_that_languages_record(self):
        for lang, needle in [("en", "Old Age Pension Scheme"), ("pa", "ਬਜ਼ੁਰਗ"), ("hi", "वृद्धावस्था")]:
            ctx = make_ctx("pension for my father" if lang == "en" else ("ਪੈਨਸ਼ਨ" if lang == "pa" else "पेंशन"), language=lang)
            text = LocalProvider().generate(ctx)
            self.assertTrue(text.strip())
            if lang != "en":
                self.assertIn(needle, text)
            self.assertIn("**", text)

    def test_intents(self):
        self.assertEqual(detect_intent("Who can apply?"), "eligibility")
        self.assertEqual(detect_intent("How do I apply?"), "apply")
        self.assertEqual(detect_intent("How much will I get?"), "benefit")
        for lang in ("en", "pa", "hi"):
            who, how, much = chat_pipeline.FOLLOW_UPS[lang]
            self.assertEqual(detect_intent(who), "eligibility", who)
            self.assertEqual(detect_intent(how), "apply", how)
            self.assertEqual(detect_intent(much), "benefit", much)

    def test_followup_answers_only_the_requested_part(self):
        hist = [ChatMessage(role="user", content="pension for my father")]
        apply_text = compose_answer(make_ctx("How do I apply?", history=hist))
        self.assertIn("How to apply", apply_text)
        self.assertNotIn("What you get", apply_text)
        benefit_text = compose_answer(make_ctx("How much will I get?", history=hist))
        self.assertIn("₹1,500", benefit_text)

    def test_no_match_and_greeting(self):
        self.assertIn("couldn't find", compose_answer(make_ctx("what is the weather")))
        self.assertIn("Sat Sri Akal", compose_answer(make_ctx("hello")))

    def test_redaction_reminder(self):
        self.assertIn("removed that number", compose_answer(make_ctx("pension, phone 9876543210")))

    def test_stream_reassembles_to_full_answer(self):
        ctx = make_ctx("pension for my father")
        self.assertEqual("".join(LocalProvider().stream(ctx)), compose_answer(ctx))

    def test_never_invents_amounts(self):
        # every rupee figure in the answer must come from the scheme record
        import re
        ctx = make_ctx("marriage grant for my daughter")
        text = compose_answer(ctx)
        record_text = json.dumps([s.model_dump() for s in ctx.schemes], ensure_ascii=False)
        for amount in re.findall(r"₹[\d,]+", text):
            self.assertIn(amount, record_text)


# ----------------------------------------------------------------- azure provider
class TestAzureProvider(unittest.TestCase):
    def provider(self, *responses, **cfg):
        p = AzureFoundryProvider(azure_settings(**cfg))
        client, completions = fake_client(*responses)
        p._client = client
        return p, completions

    def test_generate_uses_deployment_and_limits(self):
        p, calls = self.provider(completion("Hello"))
        self.assertEqual(p.generate(make_ctx()), "Hello")
        sent = calls.calls[0]
        self.assertEqual(sent["model"], "jansaathi-gpt")
        self.assertEqual(sent["max_completion_tokens"], settings.model_max_tokens)
        self.assertFalse(sent["stream"])
        self.assertEqual(sent["messages"][0]["role"], "system")

    def test_temperature_omitted_when_blank(self):
        p, calls = self.provider(completion("ok"), model_temperature=None)
        p.generate(make_ctx())
        self.assertNotIn("temperature", calls.calls[0])

    def test_learns_to_drop_temperature(self):
        err = FakeBadRequest("Unsupported value: 'temperature' does not support 0.2 with this model.")
        p, calls = self.provider(err, completion("ok"), completion("ok again"), model_temperature=0.2)
        self.assertEqual(p.generate(make_ctx()), "ok")
        self.assertIn("temperature", calls.calls[0])
        self.assertNotIn("temperature", calls.calls[1])
        p.generate(make_ctx())                      # remembered: first try succeeds
        self.assertNotIn("temperature", calls.calls[2])
        self.assertEqual(len(calls.calls), 3)

    def test_switches_token_parameter(self):
        err = FakeBadRequest("Unsupported parameter: 'max_completion_tokens' is not supported. Use 'max_tokens' instead.")
        p, calls = self.provider(err, completion("ok"))
        p.generate(make_ctx())
        self.assertIn("max_completion_tokens", calls.calls[0])
        self.assertIn("max_tokens", calls.calls[1])
        self.assertNotIn("max_completion_tokens", calls.calls[1])

    def test_other_errors_are_raised(self):
        p, _ = self.provider(FakeServerError("boom"))
        with self.assertRaises(FakeServerError):
            p.generate(make_ctx())
        p, _ = self.provider(FakeBadRequest("Invalid API key"))
        with self.assertRaises(FakeBadRequest):
            p.generate(make_ctx())

    def test_empty_answer_is_an_error(self):
        p, _ = self.provider(completion("   "))
        with self.assertRaises(ProviderError):
            p.generate(make_ctx())

    def test_stream_skips_empty_choice_chunks(self):
        events = iter([chunk(empty=True), chunk("Hel"), chunk("lo"), chunk(None, finish="stop")])
        p, calls = self.provider(events)
        self.assertEqual("".join(p.stream(make_ctx())), "Hello")
        self.assertTrue(calls.calls[0]["stream"])

    def test_stream_content_filter_raises(self):
        p, _ = self.provider(iter([chunk(None, finish="content_filter")]))
        with self.assertRaises(ProviderError):
            list(p.stream(make_ctx()))

    def test_ping(self):
        p, _ = self.provider(completion("ok", model="gpt-x"))
        result = p.ping()
        self.assertTrue(result["ok"])
        self.assertEqual(result["deployment"], "jansaathi-gpt")
        self.assertEqual(result["auth"], "api_key")


# ----------------------------------------------------------------- facade + fallback
class TestAiService(unittest.TestCase):
    def setUp(self):
        self._saved = (settings.ai_provider, settings.azure_endpoint, settings.azure_deployment, settings.azure_api_key)
        ai_service._azure = None

    def tearDown(self):
        (settings.ai_provider, settings.azure_endpoint, settings.azure_deployment, settings.azure_api_key) = self._saved
        ai_service._azure = None

    def use_azure(self, *responses):
        settings.ai_provider = "azure"
        settings.azure_endpoint = "https://demo.openai.azure.com/"
        settings.azure_deployment = "d"
        settings.azure_api_key = "k"
        provider = AzureFoundryProvider(settings)
        client, calls = fake_client(*responses)
        provider._client = client
        ai_service._azure = provider
        return calls

    def test_local_by_default(self):
        settings.ai_provider = "local"
        result = ai_service.generate_chat(make_ctx())
        self.assertEqual((result.provider, result.degraded), ("local", False))
        self.assertFalse(ai_service.is_ai_ready())

    def test_azure_success(self):
        self.use_azure(completion("From Azure"))
        result = ai_service.generate_chat(make_ctx())
        self.assertEqual((result.text, result.provider, result.degraded), ("From Azure", "azure", False))
        self.assertTrue(ai_service.is_ai_ready())

    def test_azure_failure_falls_back_to_local(self):
        self.use_azure(FakeServerError("azure down"))
        result = ai_service.generate_chat(make_ctx("pension for my father"))
        self.assertEqual((result.provider, result.degraded), ("local", True))
        self.assertIn("Old Age Pension Scheme", result.text)

    def test_stream_azure(self):
        self.use_azure(iter([chunk("Sat "), chunk("Sri "), chunk("Akal", finish="stop")]))
        stream = ai_service.open_stream(make_ctx())
        self.assertEqual("".join(stream), "Sat Sri Akal")
        self.assertEqual((stream.provider, stream.degraded, stream.interrupted), ("azure", False, False))

    def test_stream_falls_back_if_azure_fails_before_first_token(self):
        self.use_azure(FakeServerError("nope"))
        stream = ai_service.open_stream(make_ctx("pension for my father"))
        text = "".join(stream)
        self.assertIn("Old Age Pension Scheme", text)
        self.assertEqual((stream.provider, stream.degraded, stream.interrupted), ("local", True, False))

    def test_stream_interrupted_midway_keeps_partial_text(self):
        def broken():
            yield chunk("Partial ")
            raise FakeServerError("connection reset")
        self.use_azure(broken())
        stream = ai_service.open_stream(make_ctx())
        self.assertEqual("".join(stream), "Partial ")
        self.assertEqual((stream.degraded, stream.interrupted), (True, True))

    def test_ping_states(self):
        settings.ai_provider = "local"
        self.assertFalse(ai_service.ping()["ok"])
        self.use_azure(completion("ok"))
        self.assertTrue(ai_service.ping()["ok"])
        self.use_azure(FakeBadRequest("Invalid API key"))
        bad = ai_service.ping()
        self.assertFalse(bad["ok"])
        self.assertNotIn("k", bad.get("api_key", ""))   # never echoes credentials

    def test_startup_report(self):
        settings.ai_provider = "azure"
        settings.azure_endpoint = ""
        self.assertIn("Falling back", ai_service.startup_report())
        settings.azure_endpoint = "https://demo.openai.azure.com/"
        settings.azure_deployment = "d"
        self.assertIn("Azure AI Foundry", ai_service.startup_report())
        settings.ai_provider = "local"
        self.assertIn("local", ai_service.startup_report())

    def test_legacy_get_chat_response_still_works(self):
        settings.ai_provider = "local"
        scheme = scheme_store.get_by_id("old-age-pension")
        text = ai_service.get_chat_response("I need pension help", "en", [], [scheme])
        self.assertIn("pension", text.lower())


# ----------------------------------------------------------------- route bodies
class TestRoutes(unittest.TestCase):
    """Calls the route functions directly (works with real FastAPI or the sandbox stand-in)."""

    def setUp(self):
        settings.ai_provider = "local"

    def test_chat_route(self):
        from app.routers import chat
        res = chat.chat(ChatRequest(message="I need a job", language="en"))
        self.assertEqual(res.matched_schemes[0].id, "ghar-ghar-rozgar")
        self.assertEqual(res.provider, "local")
        self.assertEqual(len(res.suggestions), 3)

    def test_chat_route_rejects_blank(self):
        from app.routers import chat
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as cm:
            chat.chat(ChatRequest(message="   ", language="en"))
        self.assertEqual(cm.exception.status_code, 422)

    def test_stream_route_event_protocol(self):
        from app.routers import chat
        response = chat.chat_stream(ChatRequest(message="pension for my father", language="en"))
        self.assertEqual(response.media_type, "text/event-stream")
        raw = "".join(response.body_iterator)
        events = [json.loads(block[len("data: "):]) for block in raw.strip().split("\n\n")]
        self.assertEqual(events[0]["type"], "meta")
        self.assertEqual(events[0]["matched_schemes"][0]["id"], "old-age-pension")
        self.assertEqual(events[-1]["type"], "done")
        self.assertEqual(len(events[-1]["suggestions"]), 3)
        self.assertTrue(all(e["type"] == "delta" for e in events[1:-1]))
        text = "".join(e["text"] for e in events[1:-1])
        self.assertIn("Old Age Pension Scheme", text)

    def test_schemes_routes_hide_internal_fields(self):
        from app.routers import schemes
        listing = schemes.list_schemes(category=None, search=None)
        self.assertEqual(listing.total, 6)
        self.assertFalse(hasattr(listing.results[0], "keywords"))
        self.assertFalse(hasattr(listing.results[0], "criteria"))
        self.assertEqual(schemes.list_schemes(category="pension", search=None).total, 1)
        self.assertEqual(schemes.list_schemes(category=None, search="ਵਿਆਹ").total, 2)   # Punjabi search works
        self.assertEqual(schemes.list_schemes(category=None, search="zzzz").total, 0)
        from fastapi import HTTPException
        with self.assertRaises(HTTPException):
            schemes.get_scheme("nope")

    def test_eligibility_and_meta_routes(self):
        from app.models.schemas import EligibilityRequest
        from app.routers import eligibility, meta
        res = eligibility.check_eligibility(
            EligibilityRequest(age=62, gender=None, category=None, situations=["punjab_resident_3y"], language="hi")
        )
        self.assertEqual(res.results[0].scheme.id, "old-age-pension")
        health = meta.health()
        self.assertEqual((health.status, health.provider, health.ai_ready, health.schemes), ("ok", "local", False, 6))
        cats = meta.categories().results
        self.assertEqual(len(cats), 6)
        self.assertEqual(sum(c.scheme_count for c in cats), 6)

    def test_app_wiring_imports(self):
        import main  # noqa: F401  (import errors here mean a broken router/module name)


if __name__ == "__main__":
    unittest.main()
