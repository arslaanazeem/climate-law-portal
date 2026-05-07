# 7. Templates and styling — turning data into HTML

A view returns a Python dictionary of data. A template turns that data into
HTML. This page explains how.

## Where the templates live

```
templates/
├── base.html                    ← outer skeleton
├── cases/
│   ├── home.html
│   ├── search_results.html
│   └── case_detail.html
└── core/
    ├── about.html
    ├── 404.html
    └── 500.html
```

## Django template syntax in 60 seconds

Templates are HTML files plus four special tags:

| Syntax | What it does | Example |
|--------|--------------|---------|
| `{{ variable }}` | Insert a value | `<h1>{{ title }}</h1>` |
| `{% tag %}` | Run a tag (control flow) | `{% if user.is_staff %} ... {% endif %}` |
| `{# comment #}` | Comment, not rendered | `{# TODO: improve heading #}` |
| `\|filter` | Transform a value | `{{ count\|intcomma }}` → "5,000" |

Common tags:

```django
{% if cases %}
  ...
{% else %}
  No cases.
{% endif %}

{% for case in cases %}
  {{ case.case_title }}
{% empty %}
  No cases.
{% endfor %}

{% url 'cases:detail' case.pk case.slug %}    ← reverse-look-up a URL
{% static 'css/site.css' %}                   ← path to a static file
{% extends 'base.html' %}                     ← inherit a parent template
{% block content %} ... {% endblock %}        ← override a parent's block
```

Common filters:

```django
{{ name|upper }}              CHRIS
{{ count|intcomma }}          5,000
{{ text|truncatechars:60 }}   "Long text…"
{{ html|linebreaksbr }}       Newlines → <br>
{{ url|urlencode }}           Safe for query strings
```

## The base template — the outer skeleton

Every page extends `base.html`, which contains:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <title>{% block title %}{{ SITE_NAME }}{% endblock %}</title>
  <link rel="stylesheet" href="{% static 'css/site.css' %}">
</head>
<body>
  <header class="site-header">
    <nav>...</nav>
  </header>
  <main>
    {% block content %}{% endblock %}
  </main>
  <footer>...</footer>
</body>
</html>
```

* `{% block title %}` and `{% block content %}` are placeholders that child
  templates fill in.
* `{% static 'css/site.css' %}` resolves to `/static/css/site.css` in dev,
  or a hashed path like `/static/css/site.2c67a6a5.css` in production.
* `{{ SITE_NAME }}` comes from our context processor in `core/context_processors.py`.

## A child template

```html
{% extends "base.html" %}

{% block title %}Search results · {{ SITE_NAME }}{% endblock %}

{% block content %}
  <h1>Results for "{{ query }}"</h1>
  <ol>
    {% for case in results %}
      <li>
        <a href="{{ case.get_absolute_url }}">{{ case.case_title }}</a>
      </li>
    {% endfor %}
  </ol>
{% endblock %}
```

Child = parent's structure + the bits inside the blocks.

## How URLs are generated

Never hard-code URLs in templates! Use `{% url %}`:

```html
<a href="{% url 'cases:home' %}">Home</a>
<a href="{% url 'cases:detail' case.pk case.slug %}">{{ case.case_title }}</a>
```

If you later rename a URL pattern, every template still works.

## The CSS file

```
static/css/site.css
```

Plain CSS, ~400 lines, no preprocessor. Top of the file:

```css
:root {
  --bg: #f6f8f7;
  --ink: #18221d;
  --brand: #0f5a3c;
  ...
}
```

These are **CSS custom properties** (variables). Change `--brand` and the
whole site's accent colour changes.

The file is organised into sections:

```
:root                 ← colour variables
body / a              ← typography
.site-header          ← top nav
.hero / .search-form  ← homepage hero
.card                 ← reusable card box
.bar-list             ← stat bars on home
.case-card            ← one entry in search results
.pagination           ← prev/next links
.case-detail          ← single-case page
.tag                  ← keyword pills
.site-footer          ← bottom bar
```

### Dark mode? Mobile?

The CSS uses simple media queries:

```css
@media (max-width: 720px) {
  .grid-2 { grid-template-columns: 1fr; }
  ...
}
```

Below 720 px the layout collapses to one column.

## Running collectstatic

In production, Django bundles every static file into a single folder so a
fast file-server (whitenoise) can serve them. The build script does:

```bash
python manage.py collectstatic --noinput
```

This copies `static/css/site.css` into `staticfiles/css/site.css`. **You
never edit `staticfiles/`** — it's regenerated on each deploy.

## Custom error pages

In `climate_law_portal/urls.py`:

```python
handler404 = "core.views.handler404"
handler500 = "core.views.handler500"
```

These point Django at our custom views, which render `core/404.html` and
`core/500.html`. The default Django error pages are ugly; ours match the
site's design.

> 🛈 **Custom 404 pages only render when DEBUG is False.**
> When `DEBUG=True` (development), Django shows its detailed error page on
> purpose so you can debug. To preview your 404, set `DJANGO_DEBUG=0`.

## Where to go next

→ [08-admin-panel.md](08-admin-panel.md) — using Django's auto-generated
admin to edit cases by hand.
