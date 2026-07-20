#!/usr/bin/env python3
"""RSS headlines (crypto + business wires) — stdlib XML parse, RSS 2.0 + Atom."""
import xml.etree.ElementTree as ET

import base


def _items(xml_text, source):
    out = []
    # Stdlib-only XXE/billion-laughs hardening (repo forbids defusedxml): legit
    # RSS/Atom never needs a DTD — reject any feed carrying entity machinery.
    head = xml_text[:4096].upper()
    if "<!DOCTYPE" in head or "<!ENTITY" in head:
        raise base.FetchError("%s: feed contains DTD/entity declarations — rejected"
                              % source)
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise base.FetchError("%s: RSS parse error %s" % (source, e))
    # RSS 2.0
    for item in root.iter("item"):
        out.append({
            "source": source,
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "published": (item.findtext("pubDate") or "").strip(),
        })
    # Atom
    ns = "{http://www.w3.org/2005/Atom}"
    for entry in root.iter(ns + "entry"):
        link_el = entry.find(ns + "link")
        out.append({
            "source": source,
            "title": (entry.findtext(ns + "title") or "").strip(),
            "link": link_el.get("href", "") if link_el is not None else "",
            "published": (entry.findtext(ns + "updated") or "").strip(),
        })
    return [i for i in out if i["title"]]


def fetch(cfg, env):
    feeds = cfg.get("feeds") or []
    if not feeds:
        raise base.FetchError("no feeds configured in sources.yaml")
    items, errors = [], []
    for url in feeds:
        source = url.split("/")[2].replace("www.", "")
        try:
            xml_text = base.http_get(url, headers={"Accept": "application/rss+xml"})
            items += _items(xml_text, source)[:25]
        except base.FetchError as e:
            errors.append(str(e)[:120])
    if not items:
        raise base.FetchError("all feeds failed: %s" % "; ".join(errors))
    return {"items": items, "feed_errors": errors}, "; ".join(feeds)
