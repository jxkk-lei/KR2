"use strict";

(() => {
    const sidebar = document.querySelector(".sidebar");
    const navToggle = document.querySelector("[data-nav-toggle]");
    const backdrop = document.querySelector(".nav-backdrop");
    const closeNavigation = () => {
        sidebar?.classList.remove("open");
        navToggle?.setAttribute("aria-expanded", "false");
        if (backdrop) backdrop.hidden = true;
        document.body.style.overflow = "";
    };
    navToggle?.addEventListener("click", () => {
        const open = !sidebar.classList.contains("open");
        sidebar.classList.toggle("open", open);
        navToggle.setAttribute("aria-expanded", String(open));
        backdrop.hidden = !open;
        document.body.style.overflow = open ? "hidden" : "";
        if (open) sidebar.querySelector("a")?.focus();
    });
    backdrop?.addEventListener("click", closeNavigation);
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && sidebar?.classList.contains("open")) {
            closeNavigation();
            navToggle?.focus();
        }
        if (event.key === "Tab" && sidebar?.classList.contains("open")) {
            const links = sidebar.querySelectorAll("a");
            const first = links[0];
            const last = links[links.length - 1];
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault(); last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault(); first.focus();
            }
        }
    });
    window.matchMedia("(min-width: 781px)").addEventListener("change", (event) => {
        if (event.matches) closeNavigation();
    });

    // Меняется только представление. Фильтрация и сортировка выполняются SQL на сервере.
    const grid = document.querySelector("[data-shipment-grid]");
    const viewButtons = document.querySelectorAll("[data-view]");
    const setView = (view) => {
        if (!grid) return;
        grid.classList.toggle("compact", view === "list");
        viewButtons.forEach((button) => {
            const selected = button.dataset.view === view;
            button.classList.toggle("selected", selected);
            button.setAttribute("aria-pressed", String(selected));
        });
    };
    try { setView(localStorage.getItem("warehouse.shipments.view") === "list" ? "list" : "grid"); }
    catch { setView("grid"); }
    viewButtons.forEach((button) => button.addEventListener("click", () => {
        const view = button.dataset.view;
        setView(view);
        try { localStorage.setItem("warehouse.shipments.view", view); } catch { /* Закрытый доступ к хранилищу не мешает переключению. */ }
    }));

    let toastTimer;
    const showToast = (message) => {
        const toast = document.querySelector(".toast");
        if (!toast) return;
        window.clearTimeout(toastTimer);
        toast.textContent = message;
        toast.hidden = false;
        toastTimer = window.setTimeout(() => { toast.hidden = true; }, 4000);
    };
    document.querySelector("[data-copy-link]")?.addEventListener("click", async () => {
        try {
            await navigator.clipboard.writeText(window.location.href);
            showToast("Ссылка на отгрузку скопирована");
        } catch {
            showToast("Скопируйте ссылку из адресной строки браузера");
        }
    });
    document.querySelector("[data-reload]")?.addEventListener("click", () => window.location.reload());
})();
