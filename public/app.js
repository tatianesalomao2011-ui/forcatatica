const API = "/api";

/* =========================
   LOGIN
========================= */

const loginPage = document.getElementById("loginPage");
const systemPage = document.getElementById("systemPage");

const loginForm = document.getElementById("loginForm");

loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
        const res = await fetch(`${API}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();

        if (data.success) {
            loginPage.classList.add("hidden");
            systemPage.classList.remove("hidden");
            loadDashboard();
            loadPoliciais();
        } else {
            alert("Usuário ou senha inválidos");
        }

    } catch (err) {
        console.error(err);
        alert("Erro no login");
    }
});

/* =========================
   LOGOUT
========================= */

document.getElementById("logoutBtn").addEventListener("click", () => {
    location.reload();
});

/* =========================
   MENU LATERAL
========================= */

const buttons = document.querySelectorAll(".menu-btn");
const pages = document.querySelectorAll(".page");

buttons.forEach(btn => {
    btn.addEventListener("click", () => {

        const target = btn.dataset.page;

        if (!target) return;

        pages.forEach(p => p.classList.remove("active-page"));
        document.getElementById(target).classList.add("active-page");

        buttons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");

    });
});

/* =========================
   DASHBOARD
========================= */

async function loadDashboard() {
    try {
        const res = await fetch(`${API}/dashboard`);
        const data = await res.json();

        document.getElementById("totalPoliciais").innerText = data.policiais;
        document.getElementById("totalAdvertencias").innerText = data.advertencias;
        document.getElementById("totalCertificados").innerText = data.certificados;
        document.getElementById("totalCursos").innerText = data.cursos;

    } catch (err) {
        console.error("Erro dashboard:", err);
    }
}

/* =========================
   POLICIAIS
========================= */

const policialForm = document.getElementById("policialForm");

policialForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const body = {
        nome: document.getElementById("nome").value,
        rgpm: document.getElementById("rgpm").value,
        discord: document.getElementById("discord").value,
        patente: document.getElementById("patente").value,
        cargo: document.getElementById("cargo").value
    };

    try {
        const res = await fetch(`${API}/policiais`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });

        const data = await res.json();

        if (data.success) {
            alert("Policial adicionado com sucesso!");
            policialForm.reset();
            loadPoliciais();
            loadDashboard();
        }

    } catch (err) {
        console.error(err);
    }
});

async function loadPoliciais() {
    try {
        const res = await fetch(`${API}/policiais`);
        const data = await res.json();

        const tbody = document.getElementById("listaPoliciais");
        tbody.innerHTML = "";

        data.forEach(p => {
            const tr = document.createElement("tr");

            tr.innerHTML = `
                <td>${p.nome}</td>
                <td>${p.patente}</td>
                <td>${p.rgpm}</td>
                <td>${p.discord_id}</td>
                <td>${p.cargo}</td>
                <td>
                    <button class="action-btn btn-delete" onclick="deletePolicial(${p.id})">Remover</button>
                </td>
            `;

            tbody.appendChild(tr);
        });

    } catch (err) {
        console.error(err);
    }
}

async function deletePolicial(id) {
    if (!confirm("Deseja remover este policial?")) return;

    await fetch(`${API}/policiais/${id}`, {
        method: "DELETE"
    });

    loadPoliciais();
    loadDashboard();
}

/* =========================
   ADVERTÊNCIAS
========================= */

document.getElementById("advertenciaForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const body = {
        tipo: document.getElementById("tipoAdvertencia").value,
        multa: document.getElementById("valorMulta").value,
        prova: document.getElementById("provaAdvertencia").value,
        policial_id: prompt("ID do policial:")
    };

    await fetch(`${API}/advertencias`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    alert("Advertência registrada!");
});

/* =========================
   CERTIFICADOS
========================= */

document.getElementById("certificadoForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const body = {
        nome_certificado: document.getElementById("nomeCertificado").value,
        assinatura: document.getElementById("assinaturaCertificado").value,
        policial_id: prompt("ID do policial:")
    };

    await fetch(`${API}/certificados`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    alert("Certificado adicionado!");
});

/* =========================
   CURSOS
========================= */

document.getElementById("cursoForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const body = {
        nome_curso: document.getElementById("nomeCurso").value,
        data_inicio: document.getElementById("dataInicio").value,
        data_fim: document.getElementById("dataFim").value,
        assinatura: document.getElementById("assinaturaCurso").value,
        policial_id: prompt("ID do policial:")
    };

    await fetch(`${API}/cursos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    alert("Curso registrado!");
});