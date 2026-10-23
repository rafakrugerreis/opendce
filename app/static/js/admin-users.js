/**
 * admin-users.js — lógica do painel de gestão de usuários.
 */

let _page = 1;
let _total = 0;
let _deleteId = null;
const LIMIT = 20;

document.addEventListener("DOMContentLoaded", () => {
  loadUsers();
  loadStats();
  setupModals();
  setupTogglePasswords();

  let debounce;
  document.getElementById("searchInput").addEventListener("input", () => {
    clearTimeout(debounce);
    debounce = setTimeout(() => {
      _page = 1;
      loadUsers();
    }, 350);
  });
  document.getElementById("statusFilter").addEventListener("change", () => {
    _page = 1;
    loadUsers();
  });

  document.getElementById("logoutBtn").addEventListener("click", () => {
    window.location.href = "/logout";
  });
  document.getElementById("sidebarToggle").addEventListener("click", () => {
    document.getElementById("sidebar").classList.toggle("collapsed");
  });

  document
    .getElementById("newUserBtn")
    .addEventListener("click", () => openModal("createModal"));
  document
    .getElementById("createSubmitBtn")
    .addEventListener("click", createUser);
  document.getElementById("editSubmitBtn").addEventListener("click", editUser);
  document
    .getElementById("resetSubmitBtn")
    .addEventListener("click", resetPassword);
  document
    .getElementById("deleteConfirmBtn")
    .addEventListener("click", deleteUser);
});

function toast(msg, type = "info") {
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
  document.getElementById("toastContainer").appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

function openModal(id) {
  document.getElementById(id).classList.add("open");
}
function closeModal(id) {
  document.getElementById(id).classList.remove("open");
}
function setupModals() {
  document.querySelectorAll("[data-close]").forEach((btn) => {
    btn.addEventListener("click", () => closeModal(btn.dataset.close));
  });
  document.querySelectorAll(".modal-overlay").forEach((overlay) => {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) closeModal(overlay.id);
    });
  });
}

function setupTogglePasswords() {
  const pairs = [
    ["tc1", "tci1", "c_senha"],
    ["te1", "tei1", "e_senha"],
    ["tr1", "tri1", "r_senha"],
  ];
  pairs.forEach(([btnId, iconId, inputId]) => {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    btn.addEventListener("click", () => {
      const el = document.getElementById(inputId);
      el.type = el.type === "password" ? "text" : "password";
      document.getElementById(iconId).className =
        el.type === "text" ? "fa-solid fa-eye-slash" : "fa-solid fa-eye";
    });
  });
}

async function loadUsers() {
  const search = encodeURIComponent(
    document.getElementById("searchInput").value.trim(),
  );
  const status = encodeURIComponent(
    document.getElementById("statusFilter").value,
  );
  const url = `/admin/users?page=${_page}&limit=${LIMIT}&search=${search}&status=${status}`;

  const res = await JWTClient.fetch(url);
  if (!res.ok) return;
  const data = await res.json();
  _total = data.total;

  renderTable(data.items);
  renderPagination(data.page, data.pages, data.total);
}

async function loadStats() {
  const [all, ativos, inativos] = await Promise.all([
    JWTClient.fetch("/admin/users?limit=1").then((r) => r.json()),
    JWTClient.fetch("/admin/users?limit=1&status=ativo").then((r) => r.json()),
    JWTClient.fetch("/admin/users?limit=1&status=inativo").then((r) =>
      r.json(),
    ),
  ]);
  document.getElementById("statTotal").textContent = all.total;
  document.getElementById("statAtivos").textContent = ativos.total;
  document.getElementById("statInativos").textContent = inativos.total;
  const allItems = await JWTClient.fetch(`/admin/users?limit=200`).then((r) =>
    r.json(),
  );
  document.getElementById("statAdmins").textContent = allItems.items.filter(
    (u) => u.is_admin,
  ).length;
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

const usersStore = new Map();

function renderTable(items) {
  const tbody = document.getElementById("usersBody");
  usersStore.clear();
  if (!items.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><i class="fa-solid fa-users-slash"></i><p>Nenhum usuário encontrado.</p></div></td></tr>`;
    return;
  }
  tbody.innerHTML = items
    .map((u) => {
      usersStore.set(u.id, u);
      const safeCracha = escapeHtml(u.cracha);
      const safeNome = escapeHtml(u.nome);
      const safeEmail = u.email ? escapeHtml(u.email) : "—";
      return `
    <tr>
      <td><code style="background:var(--bg-input);padding:2px 8px;border-radius:6px;font-size:0.82rem;">${safeCracha}</code></td>
      <td><strong>${safeNome}</strong></td>
      <td style="color:var(--text-muted);">${safeEmail}</td>
      <td>${u.is_admin ? '<span class="badge badge-admin">🛡️ Admin</span>' : '<span class="badge badge-user">👤 Usuário</span>'}</td>
      <td>${u.is_active ? '<span class="badge badge-active">● Ativo</span>' : '<span class="badge badge-inactive">● Inativo</span>'}</td>
      <td>${u.password_changed ? '<span class="badge badge-active" style="font-size:0.7rem;">✓ Definida</span>' : '<span class="badge badge-inactive" style="font-size:0.7rem;">⚠ Temp</span>'}</td>
      <td>
        <div class="actions">
          <button class="btn-action" title="Editar" onclick="openEditModalById(${u.id})">
            <i class="fa-solid fa-pen"></i>
          </button>
          <button class="btn-action warn" title="Resetar senha" onclick="openResetModal(${u.id})">
            <i class="fa-solid fa-rotate"></i>
          </button>
          <button class="btn-action danger" title="Excluir" onclick="openDeleteModalById(${u.id})">
            <i class="fa-solid fa-trash"></i>
          </button>
        </div>
      </td>
    </tr>`;
    })
    .join("");
}

function openEditModalById(id) {
  const u = usersStore.get(id);
  if (!u) return;
  openEditModal(u.id, u.nome, u.email || "", u.is_active, u.is_admin);
}

function openDeleteModalById(id) {
  const u = usersStore.get(id);
  if (!u) return;
  openDeleteModal(u.id, u.nome);
}

function renderPagination(page, pages, total) {
  const el = document.getElementById("pagination");
  const info = document.getElementById("paginationInfo");
  const ctrl = document.getElementById("paginationControls");
  if (total === 0) {
    el.style.display = "none";
    return;
  }
  el.style.display = "flex";
  const from = (page - 1) * LIMIT + 1;
  const to = Math.min(page * LIMIT, total);
  info.textContent = `${from}–${to} de ${total}`;
  const btns = [];
  btns.push(
    `<button class="btn-page" ${page === 1 ? "disabled" : ""} onclick="_changePage(${page - 1})"><i class="fa-solid fa-chevron-left"></i></button>`,
  );
  for (let p = Math.max(1, page - 2); p <= Math.min(pages, page + 2); p++) {
    btns.push(
      `<button class="btn-page ${p === page ? "active" : ""}" onclick="_changePage(${p})">${p}</button>`,
    );
  }
  btns.push(
    `<button class="btn-page" ${page === pages ? "disabled" : ""} onclick="_changePage(${page + 1})"><i class="fa-solid fa-chevron-right"></i></button>`,
  );
  ctrl.innerHTML = btns.join("");
}

function _changePage(p) {
  _page = p;
  loadUsers();
}

async function createUser() {
  const body = {
    nome: document.getElementById("c_nome").value.trim(),
    cracha: document.getElementById("c_cracha").value.trim(),
    senha: document.getElementById("c_senha").value,
    email: document.getElementById("c_email").value.trim() || null,
    is_admin: document.getElementById("c_admin").checked,
  };
  if (!body.nome || !body.cracha || !body.senha) {
    toast("Preencha todos os campos obrigatórios.", "error");
    return;
  }
  if (body.senha.length < 8) {
    toast("Senha deve ter pelo menos 8 caracteres.", "error");
    return;
  }

  const res = await JWTClient.fetch("/admin/users", {
    method: "POST",
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    toast(data.detail || "Erro ao criar usuário.", "error");
    return;
  }
  toast(`Usuário ${data.nome} criado com sucesso!`, "success");
  closeModal("createModal");
  document.getElementById("c_nome").value = "";
  document.getElementById("c_cracha").value = "";
  document.getElementById("c_senha").value = "";
  document.getElementById("c_email").value = "";
  document.getElementById("c_admin").checked = false;
  loadUsers();
  loadStats();
}

function openEditModal(id, nome, email, isActive, isAdmin) {
  document.getElementById("e_id").value = id;
  document.getElementById("e_nome").value = nome;
  document.getElementById("e_email").value = email;
  document.getElementById("e_active").checked = isActive;
  document.getElementById("e_admin").checked = isAdmin;
  document.getElementById("e_senha").value = "";
  openModal("editModal");
}

async function editUser() {
  const id = document.getElementById("e_id").value;
  const body = {
    nome: document.getElementById("e_nome").value.trim(),
    email: document.getElementById("e_email").value.trim() || null,
    is_active: document.getElementById("e_active").checked,
    is_admin: document.getElementById("e_admin").checked,
  };
  const senha = document.getElementById("e_senha").value;
  if (senha) {
    if (senha.length < 8) {
      toast("Senha deve ter pelo menos 8 caracteres.", "error");
      return;
    }
    body.senha = senha;
  }

  const res = await JWTClient.fetch(`/admin/users/${id}`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    toast(data.detail || "Erro ao editar.", "error");
    return;
  }
  toast("Usuário atualizado!", "success");
  closeModal("editModal");
  loadUsers();
}

function openResetModal(id) {
  document.getElementById("r_id").value = id;
  document.getElementById("r_senha").value = "";
  openModal("resetModal");
}

async function resetPassword() {
  const id = document.getElementById("r_id").value;
  const senha = document.getElementById("r_senha").value;
  if (senha.length < 8) {
    toast("Senha deve ter pelo menos 8 caracteres.", "error");
    return;
  }

  const res = await JWTClient.fetch(`/admin/users/${id}/reset-password`, {
    method: "POST",
    body: JSON.stringify({ nova_senha: senha }),
  });
  if (!res.ok) {
    toast("Erro ao resetar senha.", "error");
    return;
  }
  toast(
    "Senha resetada! Usuário deverá criar nova senha no próximo acesso.",
    "success",
  );
  closeModal("resetModal");
  loadUsers();
}

function openDeleteModal(id, nome) {
  _deleteId = id;
  document.getElementById("deleteUserName").textContent = nome;
  openModal("deleteModal");
}

async function deleteUser() {
  if (!_deleteId) return;
  const res = await JWTClient.fetch(`/admin/users/${_deleteId}?confirm=true`, {
    method: "DELETE",
  });
  const data = await res.json();
  if (!res.ok) {
    toast(data.detail || "Erro ao excluir.", "error");
    return;
  }
  toast("Usuário excluído.", "success");
  closeModal("deleteModal");
  _deleteId = null;
  loadUsers();
  loadStats();
}
