# 8. The admin panel — editing cases without code

Django gives you a fully-working admin interface for your data, **for free**.
You log in, you see lists of every model, and you can add / edit / delete /
search rows in a polished UI. No code needed beyond a few config lines.

## Where to find it

```
http://127.0.0.1:8000/admin/
```

Or in production: `https://your-app.onrender.com/admin/`.

## Getting in for the first time

You need an admin user (called a **superuser**). Create one once with:

```powershell
python manage.py createsuperuser
```

It prompts for:

```
Username: admin
Email:    you@example.com
Password: (typed silently)
Password (again):
```

Then log in at `/admin/`.

## What you see after logging in

* A sidebar with sections — **CASES**, **AUTHENTICATION AND AUTHORIZATION**.
* Under "Cases" → "Cases": a paginated list of every row, with filters.
* Click any case to edit it. Click "Add" (top right) to create a new one.
* "Save" / "Save and continue editing" / "Save and add another" buttons.

## How the admin is configured

In `cases/admin.py`:

```python
@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("case_title", "court", "year", "violation_type", "country", "created_at")
    list_filter = ("violation_type", "year", "country", "court")
    search_fields = ("case_title", "court", "summary", "full_text", "tags")
    readonly_fields = ("created_at", "updated_at")
    prepopulated_fields = {"slug": ("case_title",)}
    date_hierarchy = "created_at"
    list_per_page = 50
    save_on_top = True
    fieldsets = (
        ("Identification", {"fields": ("case_title", "slug", "court", "country", "year")}),
        ("Classification", {"fields": ("violation_type", "tags")}),
        ("Content",        {"fields": ("summary", "full_text")}),
        ("Provenance",     {"classes": ("collapse",), "fields": ("source_file", "created_at", "updated_at")}),
    )
```

What each line does:

| Setting | What it does |
|---------|--------------|
| `list_display` | Columns shown on the list page |
| `list_filter` | Right-hand sidebar filters (clickable) |
| `search_fields` | Fields the search box at the top searches |
| `readonly_fields` | Fields shown but not editable on the edit form |
| `prepopulated_fields` | Auto-fill the slug from the title as you type |
| `date_hierarchy` | Year/month/day drill-down at the top of the list |
| `list_per_page` | Pagination — 50 rows per page on the list view |
| `save_on_top` | Show "Save" buttons at the top of the form, not just the bottom |
| `fieldsets` | Group fields into collapsible sections on the edit form |

## What the admin can do (out of the box)

* ✅ List, search, filter every case
* ✅ Add a new case with a friendly form
* ✅ Edit any field; preview slug; choose violation type from a dropdown
* ✅ Delete one or many cases at once
* ✅ Bulk actions (e.g. "Delete selected")
* ✅ View change history (every save is logged)
* ✅ User and group management (under "Authentication and Authorization")
* ✅ Permission system — give other users limited access without code

## Common admin tasks

### Add a single case manually

1. `/admin/cases/case/add/`
2. Fill the form (case_title is required; the rest is optional).
3. Click "Save".

### Search for a case

Type any keyword into the search box at the top of the case list. It searches
`case_title`, `court`, `summary`, `full_text`, and `tags`.

### Bulk-delete cases (DANGER)

1. Tick the boxes next to cases you want to remove (or "Select all" at the top).
2. Action dropdown → "Delete selected cases".
3. Confirm.

### Make a colleague a "staff" user (limited admin)

1. Authentication and Authorization → Users → "Add user".
2. Set username + password.
3. On the next page, tick "Staff status" (NOT "Superuser status").
4. Add them to a Group with the right permissions, **or** tick individual
   permissions like `cases.change_case`.

## Customising the admin

A few easy enhancements you can make to `cases/admin.py`:

### Add a custom column

```python
list_display = (..., "tag_count")

def tag_count(self, obj):
    return len(obj.tag_list)
tag_count.short_description = "Tags"
```

### Add a custom action

```python
@admin.action(description="Mark selected cases as 'other'")
def reset_violation(self, request, queryset):
    queryset.update(violation_type="other")

actions = [reset_violation]
```

### Make a field clickable to edit

```python
list_display_links = ("case_title",)
```

## Where to go next

→ [09-importing-data.md](09-importing-data.md) — bulk-loading data from
text, CSV or JSON files.
