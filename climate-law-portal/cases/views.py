"""Views for the cases app: home, search results, case detail."""
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import Case, VIOLATION_CHOICES


def home_view(request):
    """Landing page — search bar, filters, recent cases, and quick stats."""
    total_cases = Case.objects.count()
    recent_cases = Case.objects.order_by("-created_at")[:8]
    by_violation = (
        Case.objects.values("violation_type")
        .annotate(n=Count("id"))
        .order_by("-n")
    )
    years = (
        Case.objects.exclude(year__isnull=True)
        .values_list("year", flat=True)
        .distinct()
        .order_by("-year")
    )
    context = {
        "total_cases": total_cases,
        "recent_cases": recent_cases,
        "by_violation": by_violation,
        "violation_choices": VIOLATION_CHOICES,
        "years": list(years),
    }
    return render(request, "cases/home.html", context)


def search_view(request):
    query = request.GET.get("q", "").strip()
    year = request.GET.get("year", "").strip()
    violation = request.GET.get("violation", "").strip()
    sort = request.GET.get("sort", "relevance").strip() or "relevance"

    qs = (
        Case.objects.all()
        .search(query)
        .filter_year(year)
        .filter_violation(violation)
    )

    if sort == "newest":
        qs = qs.order_by("-year", "-created_at")
    elif sort == "oldest":
        qs = qs.order_by("year", "created_at")
    elif sort == "title":
        qs = qs.order_by("case_title")
    else:  # relevance — fall back to year desc
        qs = qs.order_by("-year", "case_title")

    paginator = Paginator(qs, settings.CASES_PER_PAGE)
    page_number = request.GET.get("page") or 1
    page = paginator.get_page(page_number)

    # Querystring used for pagination links — preserves all filters except `page`.
    base_qs = request.GET.copy()
    base_qs.pop("page", None)
    base_querystring = base_qs.urlencode()

    context = {
        "query": query,
        "year": year,
        "violation": violation,
        "sort": sort,
        "page_obj": page,
        "paginator": paginator,
        "results": page.object_list,
        "total_results": paginator.count,
        "violation_choices": VIOLATION_CHOICES,
        "years": list(
            Case.objects.exclude(year__isnull=True)
            .values_list("year", flat=True)
            .distinct()
            .order_by("-year")
        ),
        "base_querystring": base_querystring,
    }
    return render(request, "cases/search_results.html", context)


def case_detail_view(request, pk: int, slug: str | None = None):
    case = get_object_or_404(Case, pk=pk)
    # Soft-redirect-style: if slug doesn't match we still serve content; this
    # avoids 404s for stale links while keeping the canonical URL discoverable.
    related = (
        Case.objects.filter(violation_type=case.violation_type)
        .exclude(pk=case.pk)
        .order_by("-year")[:5]
    )
    return render(
        request,
        "cases/case_detail.html",
        {"case": case, "related": related},
    )


def case_detail_by_pk_only(request, pk: int):
    """Fallback URL without a slug — useful for short links."""
    case = get_object_or_404(Case, pk=pk)
    return case_detail_view(request, pk=pk, slug=case.slug)
