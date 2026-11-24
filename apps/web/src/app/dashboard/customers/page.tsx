"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Customer = {
  id: string;
  full_name: string;
  email: string;
  phone: string | null;
  source: string | null;
  created_at: string;
};

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Customer[]>("/api/v1/crm/customers", token)
      .then(setCustomers)
      .catch(() => setError("Could not load customers."));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Customers</h1>
      <p className="mt-2 text-sm text-slate-600">CRM records with deduplication by email.</p>
      {error && <p className="mt-4 text-sm text-amber-700">{error}</p>}
      {customers.length === 0 ? (
        <p className="mt-8 text-sm text-slate-500">No customers yet.</p>
      ) : (
        <table className="mt-8 w-full text-left text-sm">
          <thead>
            <tr className="border-b text-slate-500">
              <th className="py-2">Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => (
              <tr key={c.id} className="border-b">
                <td className="py-2 font-medium">{c.full_name}</td>
                <td>{c.email}</td>
                <td>{c.phone ?? "—"}</td>
                <td>{c.source ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}