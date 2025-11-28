import { callApi } from "./apiService.js";

document.addEventListener("DOMContentLoaded", () => {
  const inputModelDir   = document.getElementById("model-dir");
  const inputModelName  = document.getElementById("model-name");

  const btnFind   = document.getElementById("btn-find-thresholds");
  const btnEval   = document.getElementById("btn-eval-test");

  const f1Micro   = document.getElementById("f1-micro");
  const f1Macro   = document.getElementById("f1-macro");
  const aucRoc    = document.getElementById("auc-roc");
  const aucPr     = document.getElementById("auc-pr");

  const tableGenres = document.getElementById("table-genres");
  const statusEval  = document.getElementById("status-eval");

  // -----------------------------
  //  Calcul des seuils (validation)
  // -----------------------------
  btnFind?.addEventListener("click", async () => {
    const modelDir  = (inputModelDir?.value || "").trim();
    const modelName = (inputModelName?.value || "").trim() || "model_poster_vers_theme";

    if (!modelDir) {
      if (statusEval) {
        statusEval.textContent = "Statut : dossier de sauvegarde du modèle manquant.";
        statusEval.classList.add("log-error");
      }
      return;
    }

    if (statusEval) {
      statusEval.textContent = "Statut : calcul des seuils en cours…";
      statusEval.classList.remove("log-error", "log-success");
    }

    const json = await callApi("/api/find_seuils",{ model_dir: modelDir, model_name: modelName },statusEval);

    if (json && json.ok && statusEval) {
      statusEval.textContent = "Statut : seuils calculés.";
      statusEval.classList.add("log-success");
    }
  });

  // -----------------------------
  //  Évaluation complète sur le test
  // -----------------------------
  btnEval?.addEventListener("click", async () => {
    if (statusEval) {
      statusEval.textContent = "Statut : évaluation en cours…";
      statusEval.classList.remove("log-error", "log-success");
    }

    const json = await callApi("/api/eval_test", {}, statusEval);
    if (!json || !json.ok) return;

    if (statusEval) {
      statusEval.textContent = "Statut : évaluation terminée.";
      statusEval.classList.add("log-success");
    }

    const [resume_global, stats_par_genre] = json.results || [];

    //métriques globales
    const g = resume_global || {};
    if (f1Micro) f1Micro.textContent = g.f1_micro != null ? g.f1_micro.toFixed(4) : "–";
    if (f1Macro) f1Macro.textContent = g.f1_macro != null ? g.f1_macro.toFixed(4) : "–";

    // tableau par genre
    const stats = stats_par_genre || {};

    const sortedEntries = Object.entries(stats).sort(
      (a, b) => (b[1].f1 ?? 0) - (a[1].f1 ?? 0)
    );

    if (tableGenres) {
      tableGenres.innerHTML = "";
      sortedEntries.forEach(([genre, s]) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${genre}</td>
          <td>${s.seuil != null ? s.seuil.toFixed(2) : "-"}</td>
          <td>${s.f1 != null ? s.f1.toFixed(3) : "-"}</td>
          <td>${s.precision != null ? s.precision.toFixed(3) : "-"}</td>
          <td>${s.recall != null ? s.recall.toFixed(3) : "-"}</td>
          <td>${s.support ?? "-"}</td>
        `;
        tableGenres.appendChild(tr);
      });
    }
  });
});
