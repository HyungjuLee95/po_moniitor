"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "../../core/api";
import { runtimeConfig } from "../../core/runtime";
import { defaultDashboardLayout } from "./widgetRegistry";
import type { DashboardLayout, WidgetId } from "./types";

function isLayout(value: unknown): value is DashboardLayout {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<DashboardLayout>;
  return Array.isArray(candidate.order) && Array.isArray(candidate.hidden)
    && (candidate.density === "comfortable" || candidate.density === "compact");
}

export function useDashboardLayout() {
  const [layout, setLayout] = useState<DashboardLayout>(defaultDashboardLayout);
  const [saved, setSaved] = useState(true);

  useEffect(() => {
    apiFetch<{ data: DashboardLayout }>("/dashboard/preferences")
      .then((payload) => {
        if (isLayout(payload.data)) setLayout(payload.data);
      })
      .catch(() => {
        const fallback = window.localStorage.getItem(runtimeConfig.layoutFallbackKey);
        if (!fallback) return;
        try {
          const parsed: unknown = JSON.parse(fallback);
          if (isLayout(parsed)) setLayout(parsed);
        } catch {
          window.localStorage.removeItem(runtimeConfig.layoutFallbackKey);
        }
      });
  }, []);

  const update = useCallback((next: DashboardLayout) => {
    setLayout(next);
    setSaved(false);
  }, []);

  const toggle = useCallback((id: WidgetId) => {
    update({
      ...layout,
      hidden: layout.hidden.includes(id)
        ? layout.hidden.filter((value) => value !== id)
        : [...layout.hidden, id],
    });
  }, [layout, update]);

  const move = useCallback((id: WidgetId, direction: -1 | 1) => {
    const index = layout.order.indexOf(id);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= layout.order.length) return;
    const order = [...layout.order];
    [order[index], order[target]] = [order[target], order[index]];
    update({ ...layout, order });
  }, [layout, update]);

  const save = useCallback(async () => {
    window.localStorage.setItem(runtimeConfig.layoutFallbackKey, JSON.stringify(layout));
    try {
      await apiFetch("/dashboard/preferences", {
        method: "PUT",
        body: JSON.stringify(layout),
      });
    } finally {
      setSaved(true);
    }
  }, [layout]);

  const reset = useCallback(() => update(defaultDashboardLayout), [update]);

  return { layout, saved, setLayout: update, toggle, move, save, reset };
}
