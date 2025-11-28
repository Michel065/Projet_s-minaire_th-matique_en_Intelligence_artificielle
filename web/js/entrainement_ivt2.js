import { callApi } from "./apiService.js";

document.addEventListener("DOMContentLoaded", () => {
  const inputSeuilRare   = document.getElementById("seuil-rare-pct");
  const inputMinCount    = document.getElementById("min-count-other");
  const inputNomOther    = document.getElementById("nom-other");

  const btnExtract       = document.getElementById("btn-extract-rare");
  const btnFusion        = document.getElementById("btn-fusion-other");

  const statusRare       = document.getElementById("status-rare");
  const listRare         = document.getElementById("list-rare");

  // 1) Calcul des thèmes rares
  btnExtract?.addEventListener("click", async () => {
    const seuilPct = parseFloat(inputSeuilRare?.value ?? "2");

    if (isNaN(seuilPct) || seuilPct < 0) {
      statusRare.textContent = "Statut : seuil rare invalide.";
      statusRare.classList.add("log-error");
      return;
    }

    statusRare.textContent = "Statut : calcul des thèmes rares en cours…";
    listRare.textContent   = "Thèmes rares : (en cours…)";

    const json = await callApi("/api/extraction_theme_rare",{ seuil: seuilPct },statusRare);

    if (json && json.ok) {
       const themes = json.themes_rares || [];
      const formatted = themes.map(t => {
        if (Array.isArray(t)) {
          const nom = t[0];
          const pct = t[1];
          const pctRounded = Number(pct).toFixed(1);
          return `${nom} (${pctRounded}%)`;
        }
        return String(t);
      });

      if (formatted.length > 0) {
        listRare.textContent =
          `Thèmes rares (${formatted.length}) : ` + formatted.join(", ");
      } else {
        listRare.textContent = "Thèmes rares : aucun.";
      }
    }
  });

  // 2) Fusion en Other
 btnFusion?.addEventListener("click", async () => {
    const minCount = parseInt(inputMinCount?.value ?? "100", 10);
    const nomOther = (inputNomOther?.value || "Other").trim() || "Other";

    if (isNaN(minCount) || minCount <= 0) {
      statusRare.textContent = "Statut : min count invalide.";
      statusRare.classList.add("log-error");
      return;
    }

    statusRare.textContent =
      `Statut : fusion des classes rares en "${nomOther}"…`;
    statusRare.classList.remove("log-error", "log-success");

    const json = await callApi("/api/fusionner_other",{seuil_min_count: minCount,nom_other: nomOther,},statusRare);

    if (!json) return;

    if (json.ok) {
      statusRare.textContent = json.message || `Statut : Genres fusionnés en "${nomOther}".`;

      const themes = json.themes_rares || [];

      const formatted = themes.map(t => {
        if (Array.isArray(t) && t.length >= 2) {
          const nom = t[0];
          const pct = Number(t[1]).toFixed(1);
          return `${nom} (${pct}%)`;
        }
        return String(t);
      });

      if (formatted.length > 0) {
        console.log(formatted)
        listRare.textContent =
          `Thèmes fusionnés dans "${nomOther}" themes_rares(${formatted.length}) : ` +
          formatted.join(", ");
      } else {
        listRare.textContent =
          `Thèmes rares : fusionnés dans "${nomOther}" (aucune entrée listée).`;
      }
    } else {
      listRare.textContent = "Thèmes rares : erreur lors de la fusion.";
    }
  });

});
