const BASE_URL = "";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(data?.detail || `Request failed (${res.status})`);
  }
  return data;
}

async function upload(path, formData, token) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(data?.detail || `Request failed (${res.status})`);
  }
  return data;
}

export const api = {
  register: (payload) =>
    request("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload) =>
    request("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: (token) =>
    request("/users/me", { headers: { Authorization: `Bearer ${token}` } }),
  searchUsers: (query, token) =>
    request(`/users/search?q=${encodeURIComponent(query)}`, {
      headers: { Authorization: `Bearer ${token}` },
    }),
  uploadPaper: ({ title, abstract, file, coAuthorIds }, token) => {
    const formData = new FormData();
    formData.append("title", title);
    formData.append("abstract", abstract);
    if (coAuthorIds?.length) formData.append("co_author_ids", coAuthorIds.join(","));
    formData.append("file", file);
    return upload("/papers", formData, token);
  },
};
