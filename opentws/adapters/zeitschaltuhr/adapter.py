"""
Zeitschaltuhr Adapter — Tages- und Jahresschaltuhr

Adapter-Konfiguration:
  latitude:             float  — Breitengrad für Sonnenauf/-untergang (default: 47.5)
  longitude:            float  — Längengrad (default: 8.0)
  altitude:             float  — Höhe ü.M. in Metern (default: 400)
  timezone:             str    — Zeitzone (leer = App-Zeitzone, z.B. "Europe/Zurich")
  holiday_country:      str    — ISO 3166-1 Ländercode (DE, AT, CH; default: CH)
  holiday_subdivision:  str    — Kanton/Bundesland (z.B. ZH, BY) — leer = Bundesfeiertage
  vacation_1_start ... vacation_6_end:  str — Ferienperioden als JJJJ-MM-TT

Binding-Konfiguration:
  timer_type:   "daily" | "annual" | "meta"
    "daily"  — Tagesschaltuhr: täglich/wöchentlich
    "annual" — Jahresschaltuhr: monatlich/jährlich
    "meta"   — Metadaten-Binding: publiziert Feiertag-/Ferienstatus automatisch

  meta_type:  (nur bei timer_type="meta")
    "none" | "holiday_today" | "holiday_tomorrow" |
    "holiday_name_today" | "holiday_name_tomorrow" |
    "vacation_1" .. "vacation_6"

  weekdays:       Liste aktiver Wochentage [0=Mo .. 6=So] (default: alle)
  months:         Liste aktiver Monate [1-12] (leer = alle; nur für annual)
  day_of_month:   Tag im Monat 0-31 (0 = alle; nur für annual)

  time_ref:       "absolute" | "sunrise" | "sunset" | "solar_noon"
  hour:           0-23 (für absolute Zeit)
  minute:         0-59
  offset_minutes: Offset in Minuten ± relativ zur Zeitreferenz

  every_hour:     bool — jede Stunde zur angegebenen Minute schalten
  every_minute:   bool — jede Minute schalten

  holiday_mode:   "ignore" | "skip" | "only" | "as_sunday"
  vacation_mode:  "ignore" | "skip" | "only" | "as_sunday"
    ignore    — Feiertage/Ferien wie Normaltage behandeln
    skip      — Nicht schalten an Feiertagen/Ferientagen
    only      — Nur an Feiertagen/Ferientagen schalten
    as_sunday — Feiertage/Ferientage wie Sonntag behandeln

  value:  Ausgabewert beim Schalten (default: "1")
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from opentws.adapters.base import AdapterBase
from opentws.adapters.registry import register

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TimerType(str, Enum):
    DAILY = "daily"
    ANNUAL = "annual"
    META = "meta"


class TimeRef(str, Enum):
    ABSOLUTE = "absolute"
    SUNRISE = "sunrise"
    SUNSET = "sunset"
    SOLAR_NOON = "solar_noon"


class HolidayMode(str, Enum):
    IGNORE = "ignore"
    SKIP = "skip"
    ONLY = "only"
    AS_SUNDAY = "as_sunday"


class MetaType(str, Enum):
    NONE = "none"
    HOLIDAY_TODAY = "holiday_today"
    HOLIDAY_TOMORROW = "holiday_tomorrow"
    HOLIDAY_NAME_TODAY = "holiday_name_today"
    HOLIDAY_NAME_TOMORROW = "holiday_name_tomorrow"
    VACATION_1 = "vacation_1"
    VACATION_2 = "vacation_2"
    VACATION_3 = "vacation_3"
    VACATION_4 = "vacation_4"
    VACATION_5 = "vacation_5"
    VACATION_6 = "vacation_6"


# ---------------------------------------------------------------------------
# Config schemas (auto-generate GUI form from Pydantic schema)
# ---------------------------------------------------------------------------

class ZeitschaltuhrConfig(BaseModel):
    latitude: float = Field(47.5, description="Breitengrad für Sonnenauf/-untergang")
    longitude: float = Field(8.0, description="Längengrad für Sonnenauf/-untergang")
    altitude: float = Field(400.0, description="Höhe ü.M. in Metern")
    timezone: str = Field("", description="Zeitzone (leer = App-Zeitzone, z.B. Europe/Zurich)")
    holiday_country: str = Field("CH", description="Feiertagsland (ISO 3166-1: DE, AT, CH, FR …)")
    holiday_subdivision: str = Field(
        "",
        description="Kanton/Bundesland (z.B. ZH, BY, OÖ) — leer = nur nationale Feiertage",
    )
    vacation_1_start: str = Field("", description="Ferienperiode 1 Beginn (JJJJ-MM-TT)")
    vacation_1_end: str = Field("", description="Ferienperiode 1 Ende (JJJJ-MM-TT)")
    vacation_2_start: str = Field("", description="Ferienperiode 2 Beginn (JJJJ-MM-TT)")
    vacation_2_end: str = Field("", description="Ferienperiode 2 Ende (JJJJ-MM-TT)")
    vacation_3_start: str = Field("", description="Ferienperiode 3 Beginn (JJJJ-MM-TT)")
    vacation_3_end: str = Field("", description="Ferienperiode 3 Ende (JJJJ-MM-TT)")
    vacation_4_start: str = Field("", description="Ferienperiode 4 Beginn (JJJJ-MM-TT)")
    vacation_4_end: str = Field("", description="Ferienperiode 4 Ende (JJJJ-MM-TT)")
    vacation_5_start: str = Field("", description="Ferienperiode 5 Beginn (JJJJ-MM-TT)")
    vacation_5_end: str = Field("", description="Ferienperiode 5 Ende (JJJJ-MM-TT)")
    vacation_6_start: str = Field("", description="Ferienperiode 6 Beginn (JJJJ-MM-TT)")
    vacation_6_end: str = Field("", description="Ferienperiode 6 Ende (JJJJ-MM-TT)")


class ZeitschaltuhrBindingConfig(BaseModel):
    timer_type: TimerType = Field(TimerType.DAILY, description="Schaltuhrentyp")
    meta_type: MetaType = Field(
        MetaType.NONE,
        description="Metadaten-Typ (nur bei timer_type=meta)",
    )

    weekdays: list[int] = Field(
        default=[0, 1, 2, 3, 4, 5, 6],
        description="Aktive Wochentage (0=Mo, 1=Di, 2=Mi, 3=Do, 4=Fr, 5=Sa, 6=So)",
    )
    months: list[int] = Field(
        default=[],
        description="Aktive Monate 1-12 (leer = alle; nur Jahresschaltuhr)",
    )
    day_of_month: int = Field(
        0,
        ge=0,
        le=31,
        description="Tag im Monat (0 = alle; nur Jahresschaltuhr)",
    )

    time_ref: TimeRef = Field(TimeRef.ABSOLUTE, description="Zeitreferenz")
    hour: int = Field(0, ge=0, le=23, description="Stunde (nur bei absoluter Zeitreferenz)")
    minute: int = Field(0, ge=0, le=59, description="Minute")
    offset_minutes: int = Field(
        0,
        description="Offset in Minuten (positiv/negativ) relativ zur Zeitreferenz",
    )

    every_hour: bool = Field(False, description="Jede Stunde zur angegebenen Minute schalten")
    every_minute: bool = Field(False, description="Jede Minute schalten")

    holiday_mode: HolidayMode = Field(HolidayMode.IGNORE, description="Feriertagsbehandlung")
    vacation_mode: HolidayMode = Field(HolidayMode.IGNORE, description="Ferienbehandlung")

    value: str = Field("1", description="Ausgabewert beim Schalten")


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

@register
class ZeitschaltuhrAdapter(AdapterBase):
    """
    Zeitschaltuhr (Timer) Adapter.

    Virtuelle Schaltuhr ohne physische Verbindung.
    Schaltet DataPoints zu konfigurierten Zeiten — mit Unterstützung für
    Wochentage, Feiertage, Ferien und astronomische Zeitpunkte
    (Sonnenaufgang/-untergang via astral).
    """

    adapter_type = "ZEITSCHALTUHR"
    config_schema = ZeitschaltuhrConfig
    binding_config_schema = ZeitschaltuhrBindingConfig

    def __init__(
        self,
        event_bus: Any,
        config: dict | None = None,
        instance_id: Any = None,
        name: str | None = None,
    ) -> None:
        super().__init__(event_bus, config, instance_id, name)
        self._cfg = ZeitschaltuhrConfig(**(config or {}))
        self._tz: Any = timezone.utc   # resolved zoneinfo.ZoneInfo in connect()
        self._task: asyncio.Task | None = None
        self._hol: Any = {}            # holidays dict-like (date → name)
        self._last_date: date | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        self._tz = await self._resolve_timezone()
        self._hol = self._build_holidays()
        self._connected = True
        await self._publish_status(True, "Zeitschaltuhr gestartet")
        self._task = asyncio.create_task(
            self._timer_loop(),
            name=f"zeitschaltuhr_{self._instance_id}",
        )
        logger.info(
            "Zeitschaltuhr '%s' gestartet (TZ=%s, Land=%s)",
            self._instance_name,
            self._tz,
            self._cfg.holiday_country,
        )

    async def disconnect(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._connected = False
        await self._publish_status(False, "Zeitschaltuhr gestoppt")

    async def _on_bindings_reloaded(self) -> None:
        if self._connected:
            now_local = datetime.now(self._tz)
            await self._publish_meta_bindings(now_local)

    # ------------------------------------------------------------------
    # Data exchange (push-only timer — no reads/writes from outside)
    # ------------------------------------------------------------------

    async def read(self, binding: Any) -> Any:
        return None

    async def write(self, binding: Any, value: Any) -> None:
        pass

    # ------------------------------------------------------------------
    # Timer loop
    # ------------------------------------------------------------------

    async def _timer_loop(self) -> None:
        """Wacht sich auf Minutengrenzen und prüft/feuert alle Schaltpunkte."""
        now_local = datetime.now(self._tz)
        await self._publish_meta_bindings(now_local)
        self._last_date = now_local.date()

        while True:
            try:
                # Sleep to the next full minute
                now_local = datetime.now(self._tz)
                sleep_secs = 60 - now_local.second + 0.1   # tiny overshoot avoids same-second re-fire
                await asyncio.sleep(sleep_secs)

                now_local = datetime.now(self._tz)
                today = now_local.date()

                # Rebuild holidays and refresh meta on day change
                if today != self._last_date:
                    self._hol = self._build_holidays()
                    await self._publish_meta_bindings(now_local)
                    self._last_date = today

                # Check each binding
                for binding in list(self._bindings):
                    try:
                        cfg = ZeitschaltuhrBindingConfig(**binding.config)
                        if cfg.timer_type != TimerType.META and self._should_fire(cfg, now_local):
                            await self._fire_binding(binding, cfg)
                    except Exception:
                        logger.exception("Fehler beim Prüfen von Binding %s", binding.id)

            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Unerwarteter Fehler in der Zeitschaltuhr-Schleife")
                await asyncio.sleep(60)

    # ------------------------------------------------------------------
    # Fire logic
    # ------------------------------------------------------------------

    def _should_fire(self, cfg: ZeitschaltuhrBindingConfig, now: datetime) -> bool:
        today = now.date()
        is_holiday = self._is_holiday(today)
        is_vacation = self._is_vacation(today)

        # Determine effective weekday (as_sunday promotion)
        effective_weekday = now.weekday()
        if is_holiday and cfg.holiday_mode == HolidayMode.AS_SUNDAY:
            effective_weekday = 6
        if is_vacation and cfg.vacation_mode == HolidayMode.AS_SUNDAY:
            effective_weekday = 6

        # Holiday gate
        if is_holiday:
            if cfg.holiday_mode == HolidayMode.SKIP:
                return False
            # ONLY → stays in flow (it is a holiday)
        else:
            if cfg.holiday_mode == HolidayMode.ONLY:
                return False

        # Vacation gate
        if is_vacation:
            if cfg.vacation_mode == HolidayMode.SKIP:
                return False
        else:
            if cfg.vacation_mode == HolidayMode.ONLY:
                return False

        # Weekday gate
        if effective_weekday not in cfg.weekdays:
            return False

        # Annual: month / day-of-month filter
        if cfg.timer_type == TimerType.ANNUAL:
            if cfg.months and now.month not in cfg.months:
                return False
            if cfg.day_of_month and now.day != cfg.day_of_month:
                return False

        # Cycling shortcuts
        if cfg.every_minute:
            return True
        if cfg.every_hour:
            return now.minute == cfg.minute

        # Absolute / astronomical target time
        target = self._calculate_target_time(cfg, today)
        if target is None:
            return False
        return now.hour == target.hour and now.minute == target.minute

    def _calculate_target_time(
        self, cfg: ZeitschaltuhrBindingConfig, for_date: date
    ) -> datetime | None:
        if cfg.time_ref == TimeRef.ABSOLUTE:
            base = datetime(
                for_date.year, for_date.month, for_date.day,
                cfg.hour, cfg.minute, tzinfo=self._tz,
            )
        else:
            base = self._get_sun_event(cfg.time_ref, for_date)
            if base is None:
                return None

        return base + timedelta(minutes=cfg.offset_minutes)

    def _get_sun_event(self, ref: TimeRef, for_date: date) -> datetime | None:
        try:
            from astral import LocationInfo
            from astral.sun import sun

            location = LocationInfo(
                name="OpenTWS",
                region="",
                timezone=str(self._tz),
                latitude=self._cfg.latitude,
                longitude=self._cfg.longitude,
            )
            s = sun(location.observer, date=for_date, tzinfo=self._tz)
            if ref == TimeRef.SUNRISE:
                return s["sunrise"]
            if ref == TimeRef.SUNSET:
                return s["sunset"]
            if ref == TimeRef.SOLAR_NOON:
                return s["noon"]
        except ImportError:
            logger.warning(
                "astral nicht installiert — Sonnenzeit-Berechnungen nicht verfügbar. "
                "Installation: pip install astral"
            )
        except Exception as exc:
            logger.warning("Sonnenzeit-Berechnung für %s fehlgeschlagen: %s", for_date, exc)
        return None

    # ------------------------------------------------------------------
    # Publish helper
    # ------------------------------------------------------------------

    async def _fire_binding(
        self, binding: Any, cfg: ZeitschaltuhrBindingConfig
    ) -> None:
        from opentws.core.event_bus import DataValueEvent

        raw = cfg.value.strip()
        if raw.lower() in ("true", "1", "on", "ein"):
            value: Any = True
        elif raw.lower() in ("false", "0", "off", "aus"):
            value = False
        else:
            try:
                value = int(raw)
            except ValueError:
                try:
                    value = float(raw)
                except ValueError:
                    value = raw

        logger.debug(
            "Zeitschaltuhr '%s': Binding %s → %r", self._instance_name, binding.id, value
        )
        await self._bus.publish(
            DataValueEvent(
                datapoint_id=binding.datapoint_id,
                value=value,
                quality="good",
                source_adapter=self.adapter_type,
                binding_id=binding.id,
            )
        )

    # ------------------------------------------------------------------
    # Meta data bindings
    # ------------------------------------------------------------------

    async def _publish_meta_bindings(self, now: datetime) -> None:
        """Publiziert Feiertag-/Ferienstatusauf alle META-Bindings."""
        today = now.date()
        tomorrow = today + timedelta(days=1)

        meta_values: dict[MetaType, Any] = {
            MetaType.HOLIDAY_TODAY: self._is_holiday(today),
            MetaType.HOLIDAY_TOMORROW: self._is_holiday(tomorrow),
            MetaType.HOLIDAY_NAME_TODAY: self._holiday_name(today),
            MetaType.HOLIDAY_NAME_TOMORROW: self._holiday_name(tomorrow),
            MetaType.VACATION_1: self._is_vacation_n(today, 1),
            MetaType.VACATION_2: self._is_vacation_n(today, 2),
            MetaType.VACATION_3: self._is_vacation_n(today, 3),
            MetaType.VACATION_4: self._is_vacation_n(today, 4),
            MetaType.VACATION_5: self._is_vacation_n(today, 5),
            MetaType.VACATION_6: self._is_vacation_n(today, 6),
        }

        from opentws.core.event_bus import DataValueEvent

        for binding in list(self._bindings):
            try:
                cfg = ZeitschaltuhrBindingConfig(**binding.config)
                if cfg.timer_type == TimerType.META and cfg.meta_type != MetaType.NONE:
                    value = meta_values.get(cfg.meta_type)
                    if value is not None:
                        await self._bus.publish(
                            DataValueEvent(
                                datapoint_id=binding.datapoint_id,
                                value=value,
                                quality="good",
                                source_adapter=self.adapter_type,
                                binding_id=binding.id,
                            )
                        )
            except Exception:
                logger.exception("Fehler beim Publishen von Meta-Binding %s", binding.id)

    # ------------------------------------------------------------------
    # Holiday helpers
    # ------------------------------------------------------------------

    def _build_holidays(self) -> Any:
        try:
            import holidays as hol_lib

            year = datetime.now().year
            kwargs: dict[str, Any] = {"years": [year, year + 1]}
            if self._cfg.holiday_subdivision:
                kwargs["subdiv"] = self._cfg.holiday_subdivision
            return hol_lib.country_holidays(self._cfg.holiday_country, **kwargs)
        except ImportError:
            logger.info(
                "holidays-Bibliothek nicht installiert — Feiertagserkennung deaktiviert "
                "(pip install holidays)"
            )
            return {}
        except Exception as exc:
            logger.warning("Feiertagskalender konnte nicht geladen werden: %s", exc)
            return {}

    def _is_holiday(self, d: date) -> bool:
        return d in self._hol

    def _holiday_name(self, d: date) -> str:
        if isinstance(self._hol, dict):
            return self._hol.get(d, "")
        try:
            return self._hol.get(d, "")
        except Exception:
            return ""

    def _parse_vacation_period(self, n: int) -> tuple[date | None, date | None]:
        start_str: str = getattr(self._cfg, f"vacation_{n}_start", "")
        end_str: str = getattr(self._cfg, f"vacation_{n}_end", "")
        try:
            start = date.fromisoformat(start_str) if start_str else None
            end = date.fromisoformat(end_str) if end_str else None
            return start, end
        except ValueError:
            return None, None

    def _is_vacation_n(self, d: date, n: int) -> bool:
        start, end = self._parse_vacation_period(n)
        if start is None or end is None:
            return False
        return start <= d <= end

    def _is_vacation(self, d: date) -> bool:
        return any(self._is_vacation_n(d, n) for n in range(1, 7))

    # ------------------------------------------------------------------
    # Timezone resolution
    # ------------------------------------------------------------------

    async def _resolve_timezone(self) -> Any:
        import zoneinfo

        tz_name = self._cfg.timezone.strip()
        if not tz_name:
            try:
                from opentws.db.database import get_db
                row = await get_db().fetchone(
                    "SELECT value FROM app_settings WHERE key='timezone'"
                )
                if row:
                    tz_name = row["value"]
            except Exception:
                pass
        if not tz_name:
            tz_name = "UTC"
        try:
            return zoneinfo.ZoneInfo(tz_name)
        except Exception:
            logger.warning("Zeitzone '%s' unbekannt — nutze UTC", tz_name)
            return timezone.utc
