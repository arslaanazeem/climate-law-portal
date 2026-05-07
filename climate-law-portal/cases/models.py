"""Case data model.

The model intentionally keeps the prompt's required fields and adds:
  - slug          → human-friendly URL
  - source_file   → original filename when ingested from disk
  - updated_at    → last modification timestamp

`tags` is stored as a comma-separated string (no extra dependency required)
and is exposed via `tag_list`/`set_tags` helpers so views can treat it as a
list. SQLite's `LIKE` is plenty for keyword search across thousands of rows.
"""
from __future__ import annotations

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


VIOLATION_CHOICES = [
    ("air_pollution", "Air Pollution"),
    ("water_pollution", "Water Pollution"),
    ("noise_pollution", "Noise Pollution"),
    ("solid_waste", "Solid Waste"),
    ("hazardous_waste", "Hazardous Waste"),
    ("deforestation", "Deforestation"),
    ("wildlife", "Wildlife / Biodiversity"),
    ("climate_change", "Climate Change"),
    ("eia_violation", "EIA / IEE Violation"),
    ("neqs_violation", "NEQS Violation"),
    ("multi_media", "Multi-Media Pollution"),
    ("other", "Other"),
]


class CaseQuerySet(models.QuerySet):
    """Custom queryset providing search and filter helpers."""

    def search(self, query: str | None):
        if not query:
            return self
        q = query.strip()
        if not q:
            return self
        return self.filter(
            models.Q(case_title__icontains=q)
            | models.Q(summary__icontains=q)
            | models.Q(full_text__icontains=q)
            | models.Q(court__icontains=q)
            | models.Q(tags__icontains=q)
        )

    def filter_year(self, year):
        if not year:
            return self
        try:
            return self.filter(year=int(year))
        except (TypeError, ValueError):
            return self

    def filter_violation(self, violation):
        if not violation:
            return self
        return self.filter(violation_type=violation)


class Case(models.Model):
    case_title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    court = models.CharField(max_length=255, blank=True, default="")
    country = models.CharField(max_length=100, default="Pakistan")
    year = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    violation_type = models.CharField(
        max_length=50,
        choices=VIOLATION_CHOICES,
        default="other",
        db_index=True,
    )
    summary = models.TextField(blank=True, default="")
    full_text = models.TextField(blank=True, default="")
    tags = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Comma-separated tags (e.g. 'NEQS, effluent, fine').",
    )
    source_file = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CaseQuerySet.as_manager()

    class Meta:
        ordering = ["-year", "case_title"]
        indexes = [
            models.Index(fields=["year"]),
            models.Index(fields=["violation_type"]),
            models.Index(fields=["country"]),
        ]
        verbose_name = "Case"
        verbose_name_plural = "Cases"

    def __str__(self) -> str:
        if self.year:
            return f"{self.case_title} ({self.year})"
        return self.case_title

    # ---- slug handling -------------------------------------------------

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._build_unique_slug()
        super().save(*args, **kwargs)

    def _build_unique_slug(self) -> str:
        base = slugify(self.case_title)[:200] or "case"
        slug = base
        n = 2
        Model = type(self)
        while Model.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{n}"
            n += 1
        return slug

    # ---- URL helpers ---------------------------------------------------

    def get_absolute_url(self) -> str:
        return reverse("cases:detail", args=[self.pk, self.slug or "case"])

    # ---- tag helpers ---------------------------------------------------

    @property
    def tag_list(self) -> list[str]:
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def set_tags(self, items) -> None:
        cleaned = []
        seen = set()
        for item in items or []:
            value = (item or "").strip()
            if value and value.lower() not in seen:
                cleaned.append(value)
                seen.add(value.lower())
        self.tags = ", ".join(cleaned)

    # ---- presentation --------------------------------------------------

    @property
    def short_summary(self) -> str:
        text = (self.summary or self.full_text or "").strip()
        if len(text) <= 280:
            return text
        return text[:277].rstrip() + "…"
