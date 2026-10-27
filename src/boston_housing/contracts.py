from pydantic import BaseModel, ConfigDict, Field


FEATURES = {
    "CRIM": {"label": "Crime rate", "unit": "per capita, by town", "min": 0, "max": 90, "default": 0.1},
    "ZN": {"label": "Large-lot zoning", "unit": "% residential land", "min": 0, "max": 100, "default": 18},
    "INDUS": {"label": "Business land", "unit": "% non-retail acres", "min": 0, "max": 30, "default": 6.9},
    "CHAS": {"label": "Charles River boundary", "unit": "0 = no, 1 = yes", "min": 0, "max": 1, "default": 0},
    "NOX": {
        "label": "Nitric oxides",
        "unit": "parts per 10 million",
        "min": 0.38,
        "max": 0.88,
        "default": 0.47,
    },
    "RM": {"label": "Rooms per dwelling", "unit": "tract average", "min": 3.5, "max": 8.8, "default": 6.4},
    "AGE": {
        "label": "Pre-1940 housing",
        "unit": "% owner-occupied units",
        "min": 0,
        "max": 100,
        "default": 50,
    },
    "DIS": {
        "label": "Employment-centre distance",
        "unit": "weighted distance index",
        "min": 1,
        "max": 12.2,
        "default": 4.5,
    },
    "RAD": {
        "label": "Highway access",
        "unit": "accessibility index (1-24)",
        "min": 1,
        "max": 24,
        "default": 4,
    },
    "TAX": {
        "label": "Property-tax rate",
        "unit": "per $10,000 full value",
        "min": 180,
        "max": 720,
        "default": 300,
    },
    "PTRATIO": {"label": "Pupil-teacher ratio", "unit": "by town", "min": 12, "max": 22.1, "default": 18},
}
FEATURE_NAMES = tuple(FEATURES)


class Scenario(BaseModel):
    model_config = ConfigDict(strict=True, allow_inf_nan=False, extra="forbid")

    CRIM: float = Field(ge=0, le=90)
    ZN: float = Field(ge=0, le=100)
    INDUS: float = Field(ge=0, le=30)
    CHAS: int = Field(ge=0, le=1)
    NOX: float = Field(ge=0.38, le=0.88)
    RM: float = Field(ge=3.5, le=8.8)
    AGE: float = Field(ge=0, le=100)
    DIS: float = Field(ge=1, le=12.2)
    RAD: int = Field(ge=1, le=24)
    TAX: float = Field(ge=180, le=720)
    PTRATIO: float = Field(ge=12, le=22.1)

    def vector(self) -> list[float]:
        return [float(getattr(self, name)) for name in FEATURE_NAMES]
