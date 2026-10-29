// Campus Café - klient-logik (taler med Flask-API'et)

const toast = document.getElementById("toast");
let toastTimer;

function visToast(besked, erFejl = false) {
    toast.textContent = besked;
    toast.classList.toggle("is-error", erFejl);
    toast.classList.add("is-visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 4500);
}

async function postJson(url, data = {}) {
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });
    const svar = await res.json();
    if (svar.login) {
        // Ikke logget ind: send til login og kom tilbage hertil bagefter
        window.location.href = `${window.LOGIN_URL}?next=${encodeURIComponent(location.pathname)}`;
        throw new Error("login");
    }
    return svar;
}

function kraeverLogin() {
    if (window.ER_LOGGET_IND) return true;
    window.location.href = `${window.LOGIN_URL}?next=${encodeURIComponent(location.pathname + location.hash)}`;
    return false;
}

// ---------- Flash-beskeder forsvinder af sig selv ----------
const flashStack = document.getElementById("flashStack");
if (flashStack) setTimeout(() => flashStack.remove(), 4000);

// ---------- Forudbestilling (dialog) ----------
const dialog = document.getElementById("bestilDialog");
if (dialog) {
    const datoVaelger = document.getElementById("bestilDato");
    let valgt = null; // { id } for dagens menu, eller { dato } for ugens plan

    // Dagens menu: vælg ret, dato kan ændres i dialogen
    document.querySelectorAll("[data-bestil]").forEach((knap) => {
        knap.addEventListener("click", () => {
            if (!kraeverLogin()) return;
            valgt = { id: Number(knap.dataset.bestil) };
            datoVaelger.disabled = false;
            datoVaelger.selectedIndex = 0;
            document.getElementById("bestilNavn").textContent = knap.dataset.navn;
            dialog.showModal();
        });
    });

    // Ugens plan: dagen er valgt på forhånd, retten følger dagen
    document.querySelectorAll("[data-bestil-dag]").forEach((knap) => {
        knap.addEventListener("click", () => {
            if (!kraeverLogin()) return;
            valgt = { dato: knap.dataset.bestilDag };
            datoVaelger.value = knap.dataset.bestilDag;
            datoVaelger.disabled = true;
            document.getElementById("bestilNavn").textContent = `${knap.dataset.navn} (${knap.dataset.label.toLowerCase()})`;
            dialog.showModal();
        });
    });

    dialog.addEventListener("close", async () => {
        if (dialog.returnValue !== "ok" || valgt === null) return;
        try {
            const svar = await postJson("/api/bestil", {
                ...valgt,
                dato: valgt.dato || datoVaelger.value,
                afhentning: document.getElementById("bestilTid").value,
            });
            visToast(svar.besked, !svar.ok);
        } catch (e) {
            if (e.message !== "login") visToast("Kunne ikke kontakte serveren.", true);
        }
    });
}

// ---------- Annuller forudbestilling (profil) ----------
document.querySelectorAll("[data-annuller]").forEach((knap) => {
    knap.addEventListener("click", async () => {
        if (!confirm("Vil du annullere denne forudbestilling?")) return;
        try {
            const svar = await postJson(`/api/bestilling/${knap.dataset.annuller}/annuller`);
            visToast(svar.besked, !svar.ok);
            if (svar.ok) knap.closest("li").remove();
        } catch (e) {
            if (e.message !== "login") visToast("Kunne ikke kontakte serveren.", true);
        }
    });
});

// ---------- Frokostmakker ----------
document.querySelectorAll("[data-makker]").forEach((slot) => {
    slot.addEventListener("click", async () => {
        if (!kraeverLogin()) return;
        try {
            const svar = await postJson("/api/makker", { tidspunkt: slot.dataset.makker });
            visToast(svar.besked, !svar.ok);
            if (svar.ok) setTimeout(() => location.reload(), 900);
        } catch (e) {
            if (e.message !== "login") visToast("Kunne ikke kontakte serveren.", true);
        }
    });
});

// ---------- Opslag ----------
const opslagForm = document.getElementById("opslagForm");
if (opslagForm) {
    opslagForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const tekst = opslagForm.tekst.value.trim();
        if (!tekst) return;
        try {
            const svar = await postJson("/api/opslag", { tekst });
            visToast(svar.besked, !svar.ok);
            if (svar.ok) setTimeout(() => location.reload(), 600);
        } catch (e) {
            if (e.message !== "login") visToast("Kunne ikke kontakte serveren.", true);
        }
    });
}

// ---------- Likes ----------
document.querySelectorAll("[data-like]").forEach((knap) => {
    knap.addEventListener("click", async () => {
        if (!kraeverLogin()) return;
        try {
            const svar = await postJson(`/api/like/${knap.dataset.like}`);
            knap.classList.toggle("is-liked", svar.liket);
            knap.querySelector("span").textContent = svar.antal;
        } catch (e) {
            if (e.message !== "login") visToast("Kunne ikke kontakte serveren.", true);
        }
    });
});

// ---------- Arrangementer ----------
document.querySelectorAll("[data-event]").forEach((knap) => {
    knap.addEventListener("click", async () => {
        if (!kraeverLogin()) return;
        knap.disabled = true;
        try {
            const svar = await postJson(`/api/event/${knap.dataset.event}`);
            visToast(svar.besked, !svar.ok);
            knap.textContent = svar.deltager ? "Afmeld" : "Deltag";
            knap.classList.toggle("btn--outline", svar.deltager);
            knap.classList.toggle("btn--primary", !svar.deltager);
            knap.closest(".event").querySelector("[data-antal]").textContent = svar.antal;
        } catch (e) {
            if (e.message !== "login") visToast("Kunne ikke kontakte serveren.", true);
        } finally {
            knap.disabled = false;
        }
    });
});

// ---------- PWA: service worker ----------
if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
}
