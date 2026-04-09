const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      detail = payload.detail || payload.message || detail;
    } catch {
      // Ignore JSON parse errors and fall back to a generic message.
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return { data: null, headers: response.headers };
  }

  return { data: await response.json(), headers: response.headers };
}

export async function listCandidates(params = {}) {
  const query = new URLSearchParams();
  if (params.name) query.set("name", params.name);
  if (params.status) query.set("status", params.status);
  if (typeof params.skip === "number") query.set("skip", String(params.skip));
  if (typeof params.limit === "number") query.set("limit", String(params.limit));
  if (params.sort_by) query.set("sort_by", params.sort_by);
  if (params.sort_order) query.set("sort_order", params.sort_order);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request(`/api/v1/candidates/${suffix}`);
}

export function createCandidate(payload) {
  return request("/api/v1/candidates/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateCandidate(id, payload) {
  return request(`/api/v1/candidates/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function patchCandidate(id, payload) {
  return request(`/api/v1/candidates/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteCandidate(id) {
  return request(`/api/v1/candidates/${id}`, {
    method: "DELETE",
  });
}

export async function loadOpenApiSpec() {
  return request("/openapi.json");
}
