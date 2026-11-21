import { createBrowserRouter, Navigate } from "react-router-dom";

import { Layout } from "@/app/Layout";
import { features } from "@/app/registry";
import NotFoundPage from "@/app/NotFoundPage";

const children = features.map((feature) => ({
  path: feature.path === "" ? undefined : feature.path,
  index: feature.path === "",
  lazy: async () => {
    const module = await feature.component();
    return { Component: module.default };
  },
}));

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      ...children,
      { path: "*", element: <NotFoundPage /> },
    ],
  },
  { path: "/index.html", element: <Navigate to="/" replace /> },
]);
