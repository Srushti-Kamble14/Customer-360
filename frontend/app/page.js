"use client";

import { useState } from "react";
import "./dashboard.css";

export default function Home() {
  const [search, setSearch] = useState("");
  const [customer, setCustomer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const searchCustomer = async () => {
    if (!search.trim()) return;

    setLoading(true);
    setError("");
    setCustomer(null);

    const API_URL =process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

    try {
  const response = await fetch(
    `${API_URL}/customers/search?email=${encodeURIComponent(search)}`
  );

      const data = await response.json();

      if (!response.ok || data.count === 0) {
        setError("No customer found with this email.");
        return;
      }

      setCustomer(data.results[0]);
    } catch (err) {
      setError("Unable to connect to Customer 360 API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="dashboard">
      {/* Header */}
      <header className="header">
        <div>
          <div className="brand">
            <span className="brand-dot"></span>
            Customer 360
          </div>

          <p className="subtitle">
            Unified customer intelligence & master data management
          </p>
        </div>

        <div className="system-status">
          <span></span>
          System Online
        </div>
      </header>

      {/* Search */}
      <section className="search-section">
        <div className="search-label">CUSTOMER SEARCH</div>

        <div className="search-box">
          <input
            type="text"
            placeholder="Search by customer email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") searchCustomer();
            }}
          />

          <button onClick={searchCustomer} disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </button>
        </div>

        <p className="search-hint">
          Search across your unified customer master
        </p>
      </section>

      {/* Error */}
      {error && <div className="error-box">{error}</div>}

      {/* Customer */}
      {customer && (
        <section className="customer-area">
          {/* Profile Header */}
          <div className="profile-header">
            <div className="avatar">
              {customer.first_name?.[0]}
              {customer.last_name?.[0]}
            </div>

            <div className="profile-title">
              <div className="verified">
                <span>●</span> MASTER CUSTOMER
              </div>

              <h1>
                {customer.first_name} {customer.last_name}
              </h1>

              <p>
                Master ID:{" "}
                <strong>{customer.master_customer_id}</strong>
              </p>
            </div>

            <div className="match-status">
              <div className="status-icon">✓</div>
              <div>
                <strong>Resolved</strong>
                <small>Entity matched</small>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="stats">
            <div className="stat-card">
              <span className="stat-label">SOURCE RECORDS</span>
              <strong>{customer.source_record_count}</strong>
            </div>

            <div className="stat-card">
              <span className="stat-label">MASTER STATUS</span>
              <strong className="green">ACTIVE</strong>
            </div>

            <div className="stat-card">
              <span className="stat-label">DATA PROFILE</span>
              <strong>COMPLETE</strong>
            </div>
          </div>

          {/* Information grid */}
          <div className="info-grid">
            {/* Personal */}
            <div className="card">
              <div className="card-header">
                <span className="card-icon">◈</span>
                <div>
                  <h2>Personal Information</h2>
                  <p>Core identity attributes</p>
                </div>
              </div>

              <div className="fields">
                <Field
                  label="First Name"
                  value={customer.first_name}
                />

                <Field
                  label="Last Name"
                  value={customer.last_name}
                />

                <Field
                  label="Date of Birth"
                  value={customer.date_of_birth}
                />
              </div>
            </div>

            {/* Contact */}
            <div className="card">
              <div className="card-header">
                <span className="card-icon">◇</span>
                <div>
                  <h2>Contact Information</h2>
                  <p>Communication details</p>
                </div>
              </div>

              <div className="fields">
                <Field label="Email" value={customer.email} />

                <Field label="Phone" value={customer.phone} />
              </div>
            </div>

            {/* Address */}
            <div className="card full-width">
              <div className="card-header">
                <span className="card-icon">⌖</span>
                <div>
                  <h2>Address</h2>
                  <p>Primary customer location</p>
                </div>
              </div>

              <div className="address-box">
                <strong>{customer.street_address}</strong>

                <span>
                  {customer.city}, {customer.postcode}
                </span>
              </div>
            </div>

            {/* Source records */}
            <div className="card full-width">
              <div className="card-header">
                <span className="card-icon">⛓</span>
                <div>
                  <h2>Source Records</h2>
                  <p>Records contributing to this master profile</p>
                </div>
              </div>

              <div className="source-records">
                {customer.source_record_count === 0 ? (
                  <span>No source records</span>
                ) : (
                  customer.source_record_ids?.map((id) => (
                    <div className="source-record" key={id}>
                      <span className="record-dot"></span>
                      <span>{id}</span>
                      <span className="record-tag">
                        SOURCE
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </section>
      )}

      {!customer && !loading && !error && (
        <div className="empty-state">
          <div className="empty-icon">◎</div>
          <h2>Search for a customer</h2>
          <p>
            Enter an email address to retrieve a unified Customer 360
            profile.
          </p>
        </div>
      )}
    </main>
  );
}

function Field({ label, value }) {
  return (
    <div className="field">
      <span>{label}</span>
      <strong>{value || "Not available"}</strong>
    </div>
  );
}