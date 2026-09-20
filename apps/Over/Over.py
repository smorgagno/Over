import json
import os
import time

from appdaemon.plugins.hass import Hass

EVENT_KINDS = ("overheating", "overpowering", "overvoltage")
PROBLEM_STATE = "on"
CLEAR_STATE = "off"


class Over(Hass):
    def initialize(self):
        self._last_alert = {}
        self._load_config()
        if not self.sensors or not self.notify_services:
            self.log(self.t("log.missing_config"))
            return
        self._subscribe_sensors()
        self.log(self.t("log.ready", count=len(self.sensors)))

    def _load_config(self):
        self.language = str(self.args.get("language") or "en").strip().lower() or "en"
        self._load_translations()
        self.sensors = self._as_list(self.args.get("over_sensors"))
        self.notify_services = self._as_list(self.args.get("notification_services"))
        self.notification_interval = self._as_int(
            self.args.get("notification_interval"), 60
        )
        self.notify_on_clear = self._as_bool(self.args.get("notify_on_clear"), False)

    def _translation_path(self, language):
        return os.path.join(os.path.dirname(__file__), "translations", f"{language}.json")

    def _read_translation_json(self, path):
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {str(key): str(value) for key, value in data.items()}

    def _load_translations(self):
        self._strings_en = self._read_translation_json(self._translation_path("en"))
        if self.language == "en":
            self._strings = dict(self._strings_en)
            self.log(self.t("log.i18n_loaded", language=self.language))
            return
        loaded = self._read_translation_json(self._translation_path(self.language))
        if not loaded:
            self._strings = dict(self._strings_en)
            self.log(self.t("log.i18n_missing", language=self.language))
            return
        self._strings = {**self._strings_en, **loaded}
        self.log(self.t("log.i18n_loaded", language=self.language))

    def t(self, key, **kwargs):
        text = self._strings.get(key)
        if text is None:
            text = self._strings_en.get(key, key)
        if not kwargs:
            return text

        class _Safe(dict):
            def __missing__(self, name):
                return "{" + name + "}"

        return text.format_map(_Safe(kwargs))

    def _subscribe_sensors(self):
        for sensor in self.sensors:
            if not self.entity_exists(sensor):
                self.log(self.t("log.missing_entity", entity=sensor))
                continue
            self.listen_state(
                self._on_problem,
                sensor,
                new=PROBLEM_STATE,
                immediate=True,
            )
            if self.notify_on_clear:
                self.listen_state(self._on_clear, sensor, new=CLEAR_STATE)

    def _on_problem(self, entity, attribute, old, new, kwargs):
        if new != PROBLEM_STATE:
            return
        if self._throttled(entity):
            self.log(self.t("log.throttled", entity=entity))
            return
        kind = self._event_kind(entity)
        name = self.friendly_name(entity) or entity
        message = self.t(f"notify.{kind}", name=name)
        self.log(message)
        self._notify(message)

    def _on_clear(self, entity, attribute, old, new, kwargs):
        if new != CLEAR_STATE:
            return
        kind = self._event_kind(entity)
        name = self.friendly_name(entity) or entity
        message = self.t(f"notify.{kind}_clear", name=name)
        self.log(message)
        self._notify(message)

    def _throttled(self, entity):
        now = time.time()
        last = self._last_alert.get(entity, 0)
        if now - last < self.notification_interval:
            return True
        self._last_alert[entity] = now
        return False

    def _event_kind(self, entity):
        name = str(entity).rsplit(".", 1)[-1].lower()
        for kind in EVENT_KINDS:
            if kind in name:
                return kind
        return "problem"

    def _notify(self, message):
        title = self.t("notify.title")
        for service_name in self.notify_services:
            service = str(service_name).strip()
            if not service:
                continue
            if "/" not in service:
                service = f"notify/{service}"
            self.call_service(service, title=title, message=message)

    @staticmethod
    def _as_list(value):
        if not value:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)

    @staticmethod
    def _as_int(value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _as_bool(value, default):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}
