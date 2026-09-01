"use client";

import { useEffect, useState } from "react";
import { checkBackendHealth } from "@/lib/api/backend";

export default function BackendTestPage() {
  const [status, setStatus] = useState("Checking backend...");
  const [data, setData] = useState<unknown>(null);

  useEffect(() => {
    checkBackendHealth()
      .then((result) => {
        setStatus("Backend connected successfully");
        setData(result);
      })
      .catch((error) => {
        setStatus("Backend connection failed");
        setData({
          error:
            error instanceof Error
              ? error.message
              : "Unknown error",
        });
      });
  }, []);

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="text-3xl font-bold">
        Backend Connection Test
      </h1>

      <p className="mt-4">
        {status}
      </p>

      {data && (
        <pre className="mt-6 overflow-auto rounded-lg border p-4 text-sm">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </main>
  );
}