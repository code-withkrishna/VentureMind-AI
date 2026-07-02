"use client";

import { useEffect } from "react";

declare var pendo: any;

export default function PendoInitializer() {
  useEffect(() => {
    if (typeof pendo !== "undefined") {
      pendo.initialize({
        visitor: {
          id: "",
        },
      });
    }
  }, []);

  return null;
}
