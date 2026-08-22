"""Reusable building blocks for the CDS paper bot."""

from .branding import EXPERIMENT_BRANDS, get_experiment_brand, render_branded_cover
from .models import (
    CoverPolicy,
    DeliveryRecord,
    ExperimentBrand,
    LifecycleStage,
    MediaSequence,
    PlatformRenderer,
    Publication,
    RenderedPost,
    lifecycle_stage_for,
)

__all__ = [
    "CoverPolicy",
    "DeliveryRecord",
    "EXPERIMENT_BRANDS",
    "ExperimentBrand",
    "LifecycleStage",
    "MediaSequence",
    "PlatformRenderer",
    "Publication",
    "RenderedPost",
    "get_experiment_brand",
    "render_branded_cover",
    "lifecycle_stage_for",
]
