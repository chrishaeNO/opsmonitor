from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path
import json


@dataclass
class PersonnelRecord:
    name: str
    radio: str
    team: str
    area: str
    planned_on: Optional[datetime] = None
    planned_off: Optional[datetime] = None
    actual_on: Optional[datetime] = None
    actual_off: Optional[datetime] = None
    
    @property
    def status(self) -> str:
        now = datetime.now()
        if self.actual_off:
            return "AVTROPP"
        if self.actual_on:
            return "PÅ JOBB"
        if self.planned_on:
            if self.planned_on <= now:
                return "FORSINKET"
            elif (self.planned_on - now) <= timedelta(minutes=60):
                return "KOMMER SNART"
        return "PLANLAGT"
    
    @property
    def delay_minutes(self) -> Optional[int]:
        if not self.planned_on:
            return None
        if self.actual_on:
            delta = self.actual_on - self.planned_on
            return int(delta.total_seconds() / 60)
        now = datetime.now()
        if now > self.planned_on:
            delta = now - self.planned_on
            return int(delta.total_seconds() / 60)
        return 0
    
    @property
    def is_late(self) -> bool:
        return self.status == "FORSINKET"


@dataclass
class AssetFile:
    title: str
    path: str
    kind: str = "file"


@dataclass
class AppConfig:
    patropp_url: str = ""
    avtropp_url: str = ""
    patropp_sheet: int = 0
    avtropp_sheet: int = 0
    theme: str = "dark"
    alarm_sound: bool = True
    columns: dict = field(default_factory=lambda: {
        "name": "Navn",
        "radio": "Sambandsnummer",
        "team": "Team",
        "area": "Område",
        "planned_on": "PlanlagtPåtropp",
        "planned_off": "PlanlagtAvtropp",
        "actual_on": "SkannetPåtropp",
        "actual_off": "Avtropp"
    })
    assets: List[AssetFile] = field(default_factory=list)
    layout: dict = field(default_factory=lambda: {
        "show_sidebar": True,
        "show_assets": True,
        "show_log": True,
        "density": "comfortable",
        "template": "2x2",
        "rows": 2,
        "cols": 2,
        "slot_assignments": {},
        "panel_order": ["status", "patropp", "avtropp", "late", "log"],
        "title": "OPD Dashboard",
    })
    branding: dict = field(default_factory=lambda: {
        "logo_primary": "",
        "logo_secondary": "",
    })
    fullscreen: bool = False
    api_base_url: str = "https://opsmonitor-alpha.vercel.app"

    def to_json(self) -> dict:
        return {
            "patropp_url": self.patropp_url,
            "avtropp_url": self.avtropp_url,
            "patropp_sheet": self.patropp_sheet,
            "avtropp_sheet": self.avtropp_sheet,
            "theme": self.theme,
            "alarm_sound": self.alarm_sound,
            "columns": self.columns,
            "assets": [{"title": a.title, "path": a.path, "kind": a.kind} for a in self.assets],
            "layout": self.layout,
            "branding": self.branding,
            "fullscreen": self.fullscreen,
            "api_base_url": self.api_base_url,
        }
    
    @classmethod
    def from_json(cls, data: dict) -> "AppConfig":
        assets = [AssetFile(**a) for a in data.get("assets", [])]
        default_columns = cls().columns
        default_layout = cls().layout
        default_branding = cls().branding
        columns = {**default_columns, **data.get("columns", {})}
        layout = {**default_layout, **data.get("layout", {})}
        branding = {**default_branding, **data.get("branding", {})}
        return cls(
            patropp_url=data.get("patropp_url", ""),
            avtropp_url=data.get("avtropp_url", ""),
            patropp_sheet=data.get("patropp_sheet", 0),
            avtropp_sheet=data.get("avtropp_sheet", 0),
            theme=data.get("theme", "dark"),
            alarm_sound=data.get("alarm_sound", True),
            columns=columns,
            assets=assets,
            layout=layout,
            branding=branding,
                fullscreen=data.get("fullscreen", False),
                api_base_url=data.get("api_base_url", "https://opsmonitor-alpha.vercel.app"),
        )


def load_config(config_file: str = "config.json") -> AppConfig:
    path = Path(config_file)
    if not path.exists():
        return AppConfig()
    try:
        return AppConfig.from_json(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return AppConfig()


def save_config(config: AppConfig, config_file: str = "config.json") -> None:
    Path(config_file).write_text(
        json.dumps(config.to_json(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
