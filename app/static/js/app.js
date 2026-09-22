/**
 * Opendce — Gerenciamento Interativo de Interface e Comunicação com a API
 */

let itemCount = 1;
let currentWizardStep = 1;

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatarCnpj(valor) {
  if (!valor) return "";
  const v = valor
    .replace(/[^A-Za-z0-9]/g, "")
    .toUpperCase()
    .slice(0, 14);
  return v
    .replace(/^([A-Z0-9]{2})([A-Z0-9])/, "$1.$2")
    .replace(/^([A-Z0-9]{2})\.([A-Z0-9]{3})([A-Z0-9])/, "$1.$2.$3")
    .replace(/\.([A-Z0-9]{3})([A-Z0-9])/, ".$1/$2")
    .replace(/([A-Z0-9]{4})([A-Z0-9]{1,2})$/, "$1-$2");
}

function formatarCpfCnpj(valor) {
  if (!valor) return "";
  const v = valor
    .replace(/[^A-Za-z0-9]/g, "")
    .toUpperCase()
    .slice(0, 14);
  if (!/[A-Z]/.test(v) && v.length <= 11) {
    return v
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
  }
  return formatarCnpj(v);
}

function aplicarMascara(el, formatFn) {
  if (!el) return;
  el.addEventListener("input", (e) => {
    e.target.value = formatFn(e.target.value);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  aplicarMascara(document.getElementById("dest_doc"), formatarCpfCnpj);
  aplicarMascara(document.getElementById("cnpj_transp"), formatarCnpj);
  aplicarMascara(document.getElementById("end_cep"), (v) =>
    v
      .replace(/\D/g, "")
      .slice(0, 8)
      .replace(/(\d{5})(\d)/, "$1-$2"),
  );

  const modTransSelect = document.getElementById("mod_trans");
  if (modTransSelect) {
    modTransSelect.addEventListener("change", (e) => {
      const transpGroup = document.getElementById("transp-cnpj-group");
      const cnpjInput = document.getElementById("cnpj_transp");
      if (transpGroup) {
        if (e.target.value === "2") {
          transpGroup.classList.remove("hidden");
          if (cnpjInput) cnpjInput.required = true;
        } else {
          transpGroup.classList.add("hidden");
          if (cnpjInput) {
            cnpjInput.required = false;
            cnpjInput.value = "";
          }
        }
      }
    });
  }

  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      const searchInput = document.getElementById("global-search");
      if (searchInput) {
        searchInput.focus();
        switchTab("management");
      }
    }
  });
  calculateItemTotals();
});

const tabTitles = {
  dashboard: "Painel Geral",
  emission: "Emissão de DC-e",
  management: "Gestão de Documentos",
};

function switchTab(tabId) {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("sidebar-item-active", btn.id === `nav-tab-${tabId}`);
  });

  document.querySelectorAll(".tab-content").forEach((content) => {
    content.classList.remove("active");
  });

  const targetTab = document.getElementById(`tab-${tabId}`);
  if (targetTab) {
    targetTab.classList.add("active");
  }

  const breadcrumb = document.getElementById("breadcrumb-current");
  if (breadcrumb && tabTitles[tabId]) {
    breadcrumb.innerText = tabTitles[tabId];
  }
}

function showToast(msg, iconName = "check_circle") {
  const toast = document.getElementById("toast");
  const msgEl = document.getElementById("toast-msg");
  const iconEl = document.getElementById("toast-icon");

  if (!toast || !msgEl) return;

  msgEl.textContent = msg;
  if (iconEl && iconName) iconEl.textContent = iconName;

  toast.classList.remove("translate-y-20", "opacity-0");
  setTimeout(() => {
    toast.classList.add("translate-y-20", "opacity-0");
  }, 2600);
}

function copyChave(chave) {
  navigator.clipboard
    .writeText(chave)
    .then(() => {
      showToast("Chave de Acesso copiada! 📋", "content_copy");
    })
    .catch(() => {
      showToast("Falha ao copiar chave", "destructive");
    });
}

function goToStep(stepNum) {
  if (stepNum < 1 || stepNum > 4) return;

  if (stepNum > 1 && currentWizardStep === 1) {
    const docInput = document.getElementById("dest_doc");
    const logrInput = document.getElementById("end_logr");
    const nroInput = document.getElementById("end_nro");
    if (
      !docInput.value.trim() ||
      !logrInput.value.trim() ||
      !nroInput.value.trim()
    ) {
      showToast("Preencha CPF/CNPJ, Logradouro e Número.", "warning");
      return;
    }
  }

  if (stepNum > 2 && currentWizardStep === 2) {
    const itemRows = document.querySelectorAll("#itens-container .item-row");
    if (itemRows.length === 0) {
      showToast("Adicione ao menos 1 item à declaração.", "warning");
      return;
    }
  }

  currentWizardStep = stepNum;

  document.querySelectorAll(".wizard-step").forEach((el) => {
    el.classList.add("hidden");
    el.classList.remove("active");
  });

  const targetStep = document.getElementById(`wizard-step-${stepNum}`);
  if (targetStep) {
    targetStep.classList.remove("hidden");
    targetStep.classList.add("active");
  }

  const progressBar = document.getElementById("stepper-progress-bar");
  if (progressBar) {
    const percentages = ["0%", "33%", "66%", "100%"];
    progressBar.style.width = percentages[stepNum - 1];
  }

  for (let i = 1; i <= 4; i++) {
    const bullet = document.getElementById(`step-bullet-${i}`);
    const label = document.getElementById(`step-label-${i}`);

    if (bullet) {
      if (i === stepNum) {
        bullet.className = "stepper-bullet stepper-bullet-active ring-4 ring-card";
        if (label)
          label.className =
            "text-xs font-bold text-primary whitespace-nowrap";
      } else if (i < stepNum) {
        bullet.className = "stepper-bullet stepper-bullet-done ring-4 ring-card";
        bullet.innerHTML =
          '<span class="material-symbols-outlined text-[18px]">check</span>';
        if (label)
          label.className =
            "text-xs font-semibold text-success whitespace-nowrap";
      } else {
        bullet.className = "stepper-bullet ring-4 ring-card";
        bullet.textContent = `${i}`;
        if (label)
          label.className =
            "text-xs font-semibold text-muted-foreground whitespace-nowrap";
      }
    }
  }

  if (stepNum === 4) {
    const destNome =
      document.getElementById("dest_nome")?.value || "Não informado";
    const destDoc = document.getElementById("dest_doc")?.value || "—";
    const logr = document.getElementById("end_logr")?.value || "";
    const nro = document.getElementById("end_nro")?.value || "";
    const mun = document.getElementById("end_mun")?.value || "";
    const uf = document.getElementById("end_uf")?.value || "";

    const revNome = document.getElementById("review-dest-nome");
    const revDoc = document.getElementById("review-dest-doc");
    const revEnd = document.getElementById("review-dest-end");

    if (revNome) revNome.textContent = destNome;
    if (revDoc) revDoc.textContent = `CPF/CNPJ: ${destDoc}`;
    if (revEnd) revEnd.textContent = `${logr}, ${nro} - ${mun}/${uf}`;
  }
}

let debounceTimerFornecedor = null;
let debounceTimerFornecedorDoc = null;
const fornecedoresCache = new Map();

function extrairEnderecoENumero(enderecoCompleto) {
  if (!enderecoCompleto) return { logradouro: "", numero: "" };
  const str = String(enderecoCompleto).trim();
  if (str.includes(",")) {
    const parts = str.split(",");
    const logradouro = parts[0].trim();
    const numero = parts.slice(1).join(",").trim();
    return { logradouro, numero: numero || "S/N" };
  }
  const match = str.match(/^(.*?)\s+(\d+[a-zA-Z]?)$/);
  if (match) {
    return { logradouro: match[1].trim(), numero: match[2].trim() };
  }
  return { logradouro: str, numero: "S/N" };
}

function formatarCep(cep) {
  if (!cep) return "";
  const clean = String(cep).replace(/\D/g, "").padStart(8, "0").slice(0, 8);
  return clean.replace(/(\d{5})(\d{3})/, "$1-$2");
}

function preencherDadosFornecedor(f) {
  if (!f) return;
  const destNome = document.getElementById("dest_nome");
  const destDoc = document.getElementById("dest_doc");
  const endLogr = document.getElementById("end_logr");
  const endNro = document.getElementById("end_nro");
  const endBairro = document.getElementById("end_bairro");
  const endCep = document.getElementById("end_cep");

  if (destNome && f.nome) destNome.value = f.nome;
  if (destDoc && f.documento) destDoc.value = formatarCpfCnpj(f.documento);

  if (f.endereco) {
    const parsed = extrairEnderecoENumero(f.endereco);
    if (endLogr) endLogr.value = parsed.logradouro;
    if (endNro) endNro.value = parsed.numero;
  }
  if (endBairro && f.bairro) endBairro.value = f.bairro;
  if (endCep && f.cep) {
    const cepFmt = formatarCep(f.cep);
    endCep.value = cepFmt;
    buscarCep(cepFmt);
  }

  showToast(`Fornecedor carregado: ${f.nome}`, "business");
}

function buscarFornecedorAutocomplete(inputEl) {
  const val = inputEl.value.trim();

  if (fornecedoresCache.has(val)) {
    preencherDadosFornecedor(fornecedoresCache.get(val));
    return;
  }

  if (val.length < 2) return;

  clearTimeout(debounceTimerFornecedor);
  debounceTimerFornecedor = setTimeout(async () => {
    try {
      const res = await fetch(`/api/fornecedores?q=${encodeURIComponent(val)}`);
      if (!res.ok) return;
      const fornecedores = await res.json();
      const datalist = document.getElementById("fornecedores-datalist");
      if (!datalist) return;
      datalist.innerHTML = "";
      fornecedores.forEach((f) => {
        fornecedoresCache.set(f.nome, f);
        if (f.documento) {
          const docLimpo = f.documento
            .replace(/[^A-Za-z0-9]/g, "")
            .toUpperCase();
          fornecedoresCache.set(docLimpo, f);
          fornecedoresCache.set(formatarCpfCnpj(f.documento), f);
        }
        const opt = document.createElement("option");
        opt.value = f.nome;
        opt.label = `${formatarCpfCnpj(f.documento || "")} - ${f.bairro || ""}`;
        datalist.appendChild(opt);
      });
      if (fornecedoresCache.has(val)) {
        preencherDadosFornecedor(fornecedoresCache.get(val));
      }
    } catch (e) {}
  }, 250);
}

function buscarFornecedorPorDoc(inputEl) {
  const val = inputEl.value.trim();
  const digits = val.replace(/[^A-Za-z0-9]/g, "").toUpperCase();

  if (fornecedoresCache.has(digits) || fornecedoresCache.has(val)) {
    preencherDadosFornecedor(
      fornecedoresCache.get(digits) || fornecedoresCache.get(val),
    );
    return;
  }

  if (digits.length < 11) return;

  clearTimeout(debounceTimerFornecedorDoc);
  debounceTimerFornecedorDoc = setTimeout(async () => {
    try {
      const res = await fetch(
        `/api/fornecedores?q=${encodeURIComponent(digits)}`,
      );
      if (!res.ok) return;
      const fornecedores = await res.json();
      if (fornecedores && fornecedores.length > 0) {
        const f = fornecedores[0];
        fornecedoresCache.set(f.nome, f);
        if (f.documento) {
          fornecedoresCache.set(
            f.documento.replace(/[^A-Za-z0-9]/g, "").toUpperCase(),
            f,
          );
          fornecedoresCache.set(formatarCpfCnpj(f.documento), f);
        }
        preencherDadosFornecedor(f);
      }
    } catch (e) {}
  }, 300);
}

let debounceTimerProduto = null;
const produtosCache = new Map();

function buscarProdutoAutocomplete(inputEl, idx) {
  const val = inputEl.value.trim();
  const ncmInput = document.querySelector(`input[name="item_ncm_${idx}"]`);

  if (produtosCache.has(val) && produtosCache.get(val) && ncmInput) {
    ncmInput.value = produtosCache.get(val);
    return;
  }

  if (val.length < 2) return;

  clearTimeout(debounceTimerProduto);
  debounceTimerProduto = setTimeout(async () => {
    try {
      const res = await fetch(`/api/produtos?q=${encodeURIComponent(val)}`);
      if (!res.ok) return;
      const produtos = await res.json();
      const datalist = document.getElementById("produtos-datalist");
      if (!datalist) return;
      datalist.innerHTML = "";
      produtos.forEach((p) => {
        if (p.ncm) {
          produtosCache.set(p.descricao, p.ncm);
        }
        const opt = document.createElement("option");
        opt.value = p.descricao;
        datalist.appendChild(opt);
      });
      if (produtosCache.has(val) && produtosCache.get(val) && ncmInput) {
        ncmInput.value = produtosCache.get(val);
      }
    } catch (e) {}
  }, 250);
}

async function resolverNcmItem(inputEl, idx) {
  const val = inputEl.value.trim();
  const ncmInput = document.querySelector(`input[name="item_ncm_${idx}"]`);
  if (!val || !ncmInput) return;

  if (produtosCache.has(val) && produtosCache.get(val)) {
    ncmInput.value = produtosCache.get(val);
    return;
  }

  try {
    const res = await fetch(
      `/api/ncm/resolver?descricao=${encodeURIComponent(val)}`,
    );
    if (!res.ok) return;
    const data = await res.json();
    if (data && data.ncm) {
      ncmInput.value = data.ncm;
      produtosCache.set(val, data.ncm);
    }
  } catch (e) {}
}

function addItem() {
  itemCount++;
  const container = document.getElementById("itens-container");
  if (!container) return;

  const itemDiv = document.createElement("div");
  itemDiv.className = "item-row card p-md relative";
  itemDiv.setAttribute("data-item", itemCount);
  itemDiv.innerHTML = `
    <div class="grid grid-cols-1 md:grid-cols-12 gap-md items-end">
      <div class="md:col-span-5">
        <label class="label label-muted uppercase tracking-wider mb-xs">
          Descrição do Item #${itemCount} *
        </label>
        <input type="text" name="item_desc_${itemCount}" required list="produtos-datalist" autocomplete="off" oninput="buscarProdutoAutocomplete(this, ${itemCount})" onchange="resolverNcmItem(this, ${itemCount})" placeholder="Digite o nome do produto cadastrado..." class="input" />
      </div>
      <div class="md:col-span-2">
        <label class="label label-muted uppercase tracking-wider mb-xs">
          Grupo NCM (2 Dígitos) *
        </label>
        <input type="text" name="item_ncm_${itemCount}" placeholder="Ex: 90" value="90" maxlength="8" class="input font-data-mono" />
      </div>
      <div class="md:col-span-2">
        <label class="label label-muted uppercase tracking-wider mb-xs">
          Quantidade *
        </label>
        <input type="number" name="item_qtd_${itemCount}" required min="0.0001" step="any" value="1" oninput="calculateItemTotals()" class="input font-data-mono" />
      </div>
      <div class="md:col-span-2">
        <label class="label label-muted uppercase tracking-wider mb-xs">
          Valor Unitário (R$) *
        </label>
        <input type="number" name="item_vun_${itemCount}" required min="0.01" step="0.01" placeholder="0.00" oninput="calculateItemTotals()" class="input font-data-mono" />
      </div>
      <div class="md:col-span-1 flex justify-end">
        <button type="button" class="btn btn-destructive btn-icon" onclick="removeItem(this)" title="Remover item">
          <span class="material-symbols-outlined text-[20px]">delete</span>
        </button>
      </div>
    </div>
  `;
  container.appendChild(itemDiv);
  calculateItemTotals();
  showToast(`Item #${itemCount} adicionado`, "add");
}

function removeItem(btn) {
  const row = btn.closest(".item-row");
  const container = document.getElementById("itens-container");
  if (container && container.querySelectorAll(".item-row").length > 1) {
    row.remove();
    calculateItemTotals();
    showToast("Item removido", "delete");
  } else {
    showToast("A declaração precisa ter no mínimo 1 item.", "warning");
  }
}

function calculateItemTotals() {
  const rows = document.querySelectorAll("#itens-container .item-row");
  let totalVal = 0;
  let totalQty = 0;

  rows.forEach((row) => {
    const qtdInput = row.querySelector("input[name^='item_qtd_']");
    const vunInput = row.querySelector("input[name^='item_vun_']");

    const qtd = parseFloat(qtdInput?.value || 0);
    const vun = parseFloat(vunInput?.value || 0);

    if (qtd > 0 && vun > 0) {
      totalQty += qtd;
      totalVal += qtd * vun;
    }
  });

  const countEl = document.getElementById("summary-items-count");
  const valEl = document.getElementById("summary-total-value");

  if (countEl) countEl.textContent = rows.length.toString();
  if (valEl) {
    valEl.textContent = totalVal.toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
    });
  }
}

async function buscarCep(cepVal) {
  const clean = (cepVal || "").replace(/\D/g, "");
  if (clean.length !== 8) return;

  try {
    const resp = await fetch(`https://viacep.com.br/ws/${clean}/json/`);
    const data = await resp.json();
    if (!data.erro) {
      const logr = document.getElementById("end_logr");
      const bairro = document.getElementById("end_bairro");
      const mun = document.getElementById("end_mun");
      const ibge = document.getElementById("end_ibge");
      const uf = document.getElementById("end_uf");

      if (logr && data.logradouro) logr.value = data.logradouro;
      if (bairro && data.bairro) bairro.value = data.bairro;
      if (mun && data.localidade) mun.value = data.localidade;
      if (ibge && data.ibge) ibge.value = data.ibge;
      if (uf && data.uf) uf.value = data.uf;

      showToast(
        `Endereço carregado: ${data.localidade}/${data.uf}`,
        "location_on",
      );
    }
  } catch (e) {
    // Silencioso em caso de falha de conexão externa
  }
}

async function submitDce(event) {
  event.preventDefault();
  const form = event.target;
  const errorBox = document.getElementById("wizard-form-destructive");
  const submitBtn = document.getElementById("btn-submit-wizard");

  if (errorBox) errorBox.classList.add("hidden");
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML =
      '<span class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span> Assinando e Emitindo...';
  }

  try {
    const formData = new FormData(form);
    const itemRows = document.querySelectorAll("#itens-container .item-row");
    const itens = [];

    itemRows.forEach((row) => {
      const idx = row.getAttribute("data-item");
      const desc = formData.get(`item_desc_${idx}`);
      const ncm = formData.get(`item_ncm_${idx}`);
      const qtd = formData.get(`item_qtd_${idx}`);
      const vun = formData.get(`item_vun_${idx}`);
      if (desc && qtd && vun) {
        itens.push({
          descricao: desc.trim(),
          ncm: ncm ? ncm.replace(/\D/g, "") : "90189099",
          quantidade: parseFloat(qtd),
          valor_unitario: parseFloat(vun),
        });
      }
    });

    if (itens.length === 0) {
      throw new Error("Adicione ao menos 1 item à declaração.");
    }

    const payload = {
      destinatario_documento:
        formData
          .get("destinatario_documento")
          ?.replace(/[^A-Za-z0-9]/g, "")
          .toUpperCase() || "",
      destinatario_nome: formData.get("destinatario_nome") || null,
      destinatario_endereco: {
        logradouro: formData.get("logradouro") || "",
        numero: formData.get("numero") || "",
        complemento: formData.get("complemento") || null,
        bairro: formData.get("bairro") || "",
        municipio_ibge: formData.get("municipio_ibge") || "4310207",
        municipio: formData.get("municipio") || "Ijuí",
        uf: formData.get("uf")?.toUpperCase() || "RS",
        cep: formData.get("cep")?.replace(/\D/g, "") || "",
        c_pais: "1058",
        x_pais: "Brasil",
      },
      itens: itens,
      modalidade_transporte: parseInt(
        formData.get("modalidade_transporte") || "1",
        10,
      ),
      cnpj_transportadora:
        formData
          .get("cnpj_transportadora")
          ?.replace(/[^A-Za-z0-9]/g, "")
          .toUpperCase() || null,
      informacoes_complementares:
        formData.get("informacoes_complementares") || null,
    };

    const resp = await fetch("/api/dce", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await resp.json();

    if (!resp.ok) {
      let msg = data.detail?.message || data.detail || "Erro ao emitir DC-e.";
      if (Array.isArray(msg)) {
        msg = msg.map((m) => m.msg || JSON.stringify(m)).join("; ");
      }
      throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
    }

    showToast(
      "DC-e emitida e assinada com sucesso! Redirecionando...",
      "verified",
    );
    setTimeout(() => {
      window.location.href = `/dce/${data.id}`;
    }, 800);
  } catch (err) {
    if (errorBox) {
      errorBox.textContent =
        err.message || "Erro inesperado ao emitir documento.";
      errorBox.classList.remove("hidden");
    } else {
      showToast(`Erro: ${err.message}`, "destructive");
    }
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML =
        '<span class="material-symbols-outlined text-[18px]">check_circle</span> Emitir e Assinar DC-e';
    }
  }
}

async function consultarStatus() {
  const box = document.getElementById("sefaz-status-box");
  const btn = document.getElementById("btn-status-sefaz");
  const terminal = document.getElementById("terminal-log-content");
  const latencyEl = document.getElementById("ws-latency-status");

  if (box) {
    box.className = "alert items-center justify-between";
    box.classList.remove("hidden");
    box.innerHTML = `
      <div class="flex items-center gap-sm text-primary">
        <span class="material-symbols-outlined animate-spin text-[20px]">sync</span>
        <span>Consultando Web Services da SEFAZ Virtual (SVRS/PR)...</span>
      </div>
    `;
  }

  if (btn) btn.disabled = true;
  const startTime = performance.now();

  try {
    const resp = await fetch("/api/status-sefaz");
    const data = await resp.json();
    const endTime = performance.now();
    const duration = Math.round(endTime - startTime);

    if (latencyEl) latencyEl.textContent = `${duration} ms`;

    if (!resp.ok) {
      const msg = escapeHtml(
        data.detail?.message || "Falha na conexão com a SEFAZ",
      );
      if (box) {
        box.className = "alert alert-destructive items-center justify-between";
        box.innerHTML = `
          <div class="flex items-center gap-sm">
            <span class="material-symbols-outlined text-destructive text-[22px]">error</span>
            <div>
              <strong>Status SEFAZ Indisponível:</strong> ${msg}
            </div>
          </div>
        `;
      }
      if (terminal) {
        const timeStr = new Date().toLocaleTimeString();
        terminal.innerHTML += `<p><span class="text-destructive">[${timeStr}]</span> GET /api/status-sefaz <span class="text-destructive">FAIL</span> · ${msg}</p>`;
      }
      return;
    }

    if (data.c_stat === "107") {
      const safeMotivo = escapeHtml(data.x_motivo || "Serviço em Operação");
      if (box) {
        box.className = "alert alert-success items-center justify-between";
        box.innerHTML = `
          <div class="flex items-center gap-sm">
            <span class="material-symbols-outlined text-success text-[22px]">check_circle</span>
            <div>
              <strong>SEFAZ em Operação (cStat 107)</strong> — ${safeMotivo} (${duration}ms)
            </div>
          </div>
          <span class="badge badge-success">
            ${data.tp_amb === "2" ? "Homologação SVRS" : "Produção"}
          </span>
        `;
      }
      if (terminal) {
        const timeStr = new Date().toLocaleTimeString();
        terminal.innerHTML += `<p><span class="text-success">[${timeStr}]</span> GET /DCeStatusServico HTTP/1.1 <span class="text-primary">200 OK</span> ${duration}ms · cStat: 107 - Serviço em Operação</p>`;
        terminal.scrollTop = terminal.scrollHeight;
      }
      showToast("SEFAZ em Operação! 🟢", "check_circle");
    } else {
      const safeMotivo = escapeHtml(data.x_motivo || "Aviso do servidor");
      const safeStat = escapeHtml(String(data.c_stat || data.http_status));
      if (box) {
        box.className = "alert alert-warning items-center justify-between";
        box.innerHTML = `
          <div class="flex items-center gap-sm">
            <span class="material-symbols-outlined text-warning text-[22px]">warning</span>
            <div>
              <strong>Retorno SEFAZ (${safeStat}):</strong> ${safeMotivo}
            </div>
          </div>
        `;
      }
    }
  } catch (err) {
    if (box) {
      const safeErr = escapeHtml(err.message);
      box.className = "alert alert-destructive items-center justify-between";
      box.innerHTML = `<div class="flex items-center gap-sm"><span class="material-symbols-outlined text-destructive">wifi_off</span> Erro de Rede: ${safeErr}</div>`;
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function transmitir(docId) {
  showToast("Iniciando transmissão para SEFAZ...", "send");

  try {
    const resp = await fetch(`/api/dce/${docId}/transmitir`, {
      method: "POST",
    });
    const data = await resp.json();

    if (!resp.ok) {
      const msg = data.detail?.message || "Erro na transmissão para SEFAZ";
      alert(`Falha na transmissão:\n${msg}`);
    } else {
      alert(
        `Retorno SEFAZ: ${data.c_stat || "OK"} - ${data.motivo || data.status}`,
      );
      window.location.reload();
    }
  } catch (err) {
    alert(`Erro ao transmitir: ${err.message}`);
  }
}

async function consultarDoc(docId) {
  showToast("Consultando protocolo na SEFAZ...", "search");

  try {
    const resp = await fetch(`/api/dce/${docId}/consultar`, { method: "POST" });
    const data = await resp.json();

    if (!resp.ok) {
      const msg = data.detail?.message || "Erro na consulta à SEFAZ";
      alert(`Falha na consulta:\n${msg}`);
    } else {
      alert(
        `Retorno SEFAZ: ${data.c_stat || "OK"} - ${data.motivo || data.status}`,
      );
      window.location.reload();
    }
  } catch (err) {
    alert(`Erro ao consultar: ${err.message}`);
  }
}

function filterTable(query) {
  const clean = (query || "").toLowerCase().replace(/\s+/g, "");
  const rows = document.querySelectorAll("#full-dce-table .doc-item-row");

  rows.forEach((row) => {
    const chave = (row.getAttribute("data-chave") || "").toLowerCase();
    const num = (row.getAttribute("data-numero") || "").toLowerCase();

    if (!clean || chave.includes(clean) || num.includes(clean)) {
      row.style.display = "";
    } else {
      row.style.display = "none";
    }
  });
}

function filterStatus(statusVal) {
  const rows = document.querySelectorAll("#full-dce-table .doc-item-row");
  rows.forEach((row) => {
    const status = row.getAttribute("data-status") || "";
    if (!statusVal || status === statusVal) {
      row.style.display = "";
    } else {
      row.style.display = "none";
    }
  });
}

function handleGlobalSearch(query) {
  switchTab("management");
  const filterInput = document.getElementById("filter-chave-table");
  if (filterInput) {
    filterInput.value = query;
  }
  filterTable(query);
}
