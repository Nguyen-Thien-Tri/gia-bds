import React, { useState } from "react";
import { initializeApp, getApps } from "firebase/app";
import {
  getFirestore,
  collection,
  getDocs,
  // The following are imported so you can uncomment sample compound queries below
  query as fbQuery,
  where,
  orderBy,
  limit as fbLimit,
  DocumentData,
} from "firebase/firestore";

/*
  INSTRUCTIONS:
  1) Replace the firebaseConfig object below with your Firebase project's config.
  2) Edit the section marked "--- EDIT QUERY BELOW ---" to write the Firestore query you want to test.
     The component will call your code when you click the "Run" button and will display results.
  3) This component uses the modular (v9) SDK.
*/

const firebaseConfig = {
  apiKey: "AIzaSyCsUb2mCviJEKisMI9oFe7pqyigKL2dzkY",
  authDomain: "real-estate-project-445516.firebaseapp.com",
  projectId: "real-estate-project-445516",
  storageBucket: "real-estate-project-445516.firebasestorage.app",
  messagingSenderId: "933297378726",
  appId: "1:933297378726:web:234baffe9ab382045a2b67",
  measurementId: "G-EP2L8DXXLJ",
};

if (!getApps().length) {
  initializeApp(firebaseConfig);
}

const db = getFirestore();

export default function TestFirestore() {
  const [docs, setDocs] = useState<Array<Record<string, any>>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      // ------------------ EDIT QUERY BELOW ------------------
      // Replace the code in this block with the query you want to test.
      // When editing, keep the same pattern: produce a Query or a QuerySnapshot
      // and then use getDocs(...) to fetch results.

      // Example (default): fetch all documents from the "test" collection
      const q = fbQuery(
        collection(db, "price_data"),
        where("province", "in", [
          "Cần Thơ",
          "Lâm Đồng",
          "Bắc Giang",
          "Quảng Trị",
          "Đà Nẵng",
          "Đồng Nai",
          "Hồ Chí Minh",
          "Thái Nguyên",
          "Hà Nội",
          // "Khánh Hòa",
          // "Bà Rịa Vũng Tàu",
        ]),
        where("bds_type", "in", ["Nhà phố", "Nhà riêng", "Căn hộ chung cư"]),
        where("year_month", "in", ["2025-11"]),
        where("price_type", "==", "Bán"),
      );
      const snap = await getDocs(q);

      // Example compound query (uncomment and adapt if needed):
      // const q = fbQuery(
      //   collection(db, "cities"),
      //   where("country", "==", "USA"),
      //   orderBy("population", "desc"),
      //   fbLimit(10)
      // );
      // const snap = await getDocs(q);

      // ------------------ END EDIT AREA ------------------

      const data = snap.docs.map((d) => ({ id: d.id, ...d.data() }));
      setDocs(data as Array<Record<string, any>>);
    } catch (e: any) {
      console.error(e);
      setError(e?.message || String(e));
      setDocs([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-semibold mb-4">Firestore Query Tester</h1>

      <div className="mb-4">
        <p className="text-sm text-gray-600">
          Edit the query code inside the component (look for "EDIT QUERY
          BELOW").
        </p>
      </div>

      <div className="flex items-center gap-3 mb-4">
        <button
          onClick={run}
          className="px-4 py-2 bg-blue-600 text-white rounded shadow-sm hover:bg-blue-700"
          disabled={loading}
        >
          {loading ? "Running..." : "Run"}
        </button>

        {error && <div className="text-red-600 text-sm">Error: {error}</div>}
      </div>

      <div className="bg-white rounded-md shadow p-4">
        <h2 className="font-medium mb-2">Documents ({docs.length})</h2>

        {docs.length === 0 ? (
          <div className="text-sm text-gray-500">
            No documents to show. Click Run to execute the query.
          </div>
        ) : (
          <ul className="space-y-3">
            {docs.map((doc) => (
              <li
                key={doc.id}
                className="border border-gray-100 rounded p-3 bg-gray-50"
              >
                <div className="text-xs text-gray-500 mb-1">id: {doc.id}</div>
                <pre className="whitespace-pre-wrap text-sm text-gray-800">
                  {JSON.stringify(doc, null, 2)}
                </pre>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="mt-4 text-xs text-gray-500">
        Tip: If you prefer to type the query in the browser, I can update this
        component to accept a query expression from a textarea.
      </div>
    </div>
  );
}
