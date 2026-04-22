from flask import redirect, render_template, request, url_for


def is_popup_request():
    return request.args.get("popup") == "1"


def popup_url_for(endpoint, **values):
    if is_popup_request():
        values.setdefault("popup", 1)
    return url_for(endpoint, **values)


def popup_redirect(endpoint, **values):
    return redirect(popup_url_for(endpoint, **values))


def popup_done(parent_url=None, refresh_parent=False):
    return render_template(
        "popup_done.html",
        parent_url=parent_url,
        refresh_parent=refresh_parent,
    )
