"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "../../core/api";
import { runtimeConfig } from "../../core/runtime";
import { defaultDashboardLayout } from "./widgetRegistry";
import type { DashboardLayout, WidgetId } from "./types";

function normalizeLayout(value: unknown): DashboardLayout | null {
  if (!value || typeof value !== "object") return null;
  const candidate = value as Partial<DashboardLayout>;
  if (!Array.isArray(candidate.order) || !Array.isArray(candidate.hidden)
    || (candidate.density !== "comfortable" && candidate.density !== "compact")) return null;
  const isLegacy = defaultDashboardLayout.order.some((id) => !candidate.order?.includes(id));
  const order = [
    ...candidate.order.filter((id): id is WidgetId => defaultDashboardLayout.order.includes(id as WidgetId)),
    ...defaultDashboardLayout.order.filter((id) => !candidate.order?.includes(id)),
  ];
  return {
    order: [...new Set(order)],
    hidden: [...new Set([
      ...candidate.hidden.filter((id): id is WidgetId => order.includes(id as WidgetId)),
      ...(isLegacy ? ["channel_status", "server_profile"] as WidgetId[] : []),
    ])],
    density: candidate.density,
    favorite_views: Array.isArray(candidate.favorite_views) ? candidate.favorite_views : [],
    recent_views: Array.isArray(candidate.recent_views) ? candidate.recent_views : [],
    view_usage: candidate.view_usage && typeof candidate.view_usage === "object"
      ? candidate.view_usage
      : {},
  };
}

export function useDashboardLayout() {
  const [layout, setLayout] = useState<DashboardLayout>(defaultDashboardLayout);
  const [saved, setSaved] = useState(true);

  useEffect(() => {
    apiFetch<{ data: DashboardLayout }>("/dashboard/preferences")
      .then((payload) => {
        const normalized = normalizeLayout(payload.data);
        if (normalized) setLayout(normalized);
      })
      .catch(() => {
        const fallback = window.localStorage.getItem(runtimeConfig.layoutFallbackKey);
        if (!fallback) return;
        try {
          const parsed: unknown = JSON.parse(fallback);
          const normalized = normalizeLayout(parsed);
          if (normalized) setLayout(normalized);
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

  const persistPreference = useCallback((next: DashboardLayout) => {
    window.localStorage.setItem(runtimeConfig.layoutFallbackKey, JSON.stringify(next));
    void apiFetch("/dashboard/preferences", {
      method: "PUT",
      body: JSON.stringify(next),
    }).catch(() => undefined);
  }, []);

  const toggleFavorite = useCallback((viewId: string) => {
    setLayout((current) => {
      const next = {
        ...current,
        favorite_views: current.favorite_views.includes(viewId)
          ? current.favorite_views.filter((id) => id !== viewId)
          : [...current.favorite_views, viewId].slice(-8),
      };
      persistPreference(next);
      return next;
    });
  }, [persistPreference]);

  const visit = useCallback((viewId: string) => {
    setLayout((current) => {
      const next = {
        ...current,
        recent_views: [viewId, ...current.recent_views.filter((id) => id !== viewId)].slice(0, 8),
        view_usage: {
          ...current.view_usage,
          [viewId]: (current.view_usage[viewId] ?? 0) + 1,
        },
      };
      persistPreference(next);
      return next;
    });
  }, [persistPreference]);

  const reset = useCallback(() => update(defaultDashboardLayout), [update]);

  return {
    layout,
    saved,
    setLayout: update,
    toggle,
    move,
    save,
    reset,
    toggleFavorite,
    visit,
  };
}
