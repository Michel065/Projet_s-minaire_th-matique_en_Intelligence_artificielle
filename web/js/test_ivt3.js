import { callApi } from "./apiService.js";
import { ImageStore, updatePreview} from "./ImageStore.js";

let lastScoresByImage = {};
let lastPerClassThresholds = null;

document.addEventListener("DOMContentLoaded", () => {
  const inputSeuilPrincipal   = document.getElementById("seuil-principal");
  const inputSeuilSecondaire  = document.getElementById("seuil-secondaire");
  const checkUsePerClass      = document.getElementById("use-per-class-thresholds");
  const btnPredict            = document.getElementById("btn-predict");
  const statusPredict         = document.getElementById("status-predict");

  const sliderTol             = document.getElementById("tol-adjust");
  const labelTol              = document.getElementById("tol-label");

  const spanImageName         = document.getElementById("current-image-name");
  const spanMainGenres        = document.getElementById("genres-principaux");
  const spanSecondaryGenres   = document.getElementById("genres-secondaires");
  const tableResults          = document.getElementById("table-results");

  const btnPrev  = document.getElementById("btn-prev-image");
  const btnNext  = document.getElementById("btn-next-image");

  function getTol() {
    if (!sliderTol) return 0;
    const v = parseFloat(sliderTol.value);
    return Number.isFinite(v) ? v : 0;
  }

  function updateTolLabel() {
    if (!labelTol) return;
    const t = getTol();
    const sign = t > 0 ? "+" : "";
    labelTol.textContent = `Ajustement : ${sign}${t.toFixed(2)}`;
  }

  function clamp01(x) {
    return Math.max(0, Math.min(1, x));
  }

  function resetResultsPlaceholder() {
    if (spanImageName)       spanImageName.textContent = "–";
    if (spanMainGenres)      spanMainGenres.textContent = "–";
    if (spanSecondaryGenres) spanSecondaryGenres.textContent = "–";

    if (tableResults) {
      tableResults.innerHTML = `
        <tr>
          <td colspan="3" style="text-align:center; opacity:0.7;">
            Les prédictions apparaîtront ici après le test.
          </td>
        </tr>`;
    }
  }

  function rerecalcFromCache() {
    const imageKey = ImageStore.getName_mais_bien();
    if (!imageKey || !lastScoresByImage[imageKey]) {
      resetResultsPlaceholder();
      return;
    }

    const entry       = lastScoresByImage[imageKey];
    const scores      = entry.scores || {};
    const perClassThr = lastPerClassThresholds;

    const baseMain = parseFloat(inputSeuilPrincipal?.value ?? "0.5");
    const baseSec  = parseFloat(inputSeuilSecondaire?.value ?? "0.3");
    const usePer   = !!(checkUsePerClass && checkUsePerClass.checked);
    const tol      = getTol();
    const factor   = 1 + tol;

    const mainGenres       = [];
    const secondaryGenres  = [];
    const allRows          = [];

    Object.entries(scores).forEach(([genre, raw]) => {
      const score = Number(raw) || 0;

      // seuil principal : soit global, soit par genre (seuils optimaux)
      let thrMain = baseMain;
      if (usePer && perClassThr && perClassThr[genre] != null) {
        thrMain = Number(perClassThr[genre]) || baseMain;
      }
      const thrSec = baseSec;

      const thrMainAdj = clamp01(thrMain * factor);
      const thrSecAdj  = clamp01(thrSec  * factor);

      let type = "Ignoré";
      if (score >= thrMainAdj) {
        type = "Principal";
        mainGenres.push({ genre, score });
      } else if (score >= thrSecAdj) {
        type = "Secondaire";
        secondaryGenres.push({ genre, score });
      }

      allRows.push({ genre, score, type });
    });

    allRows.sort((a, b) => b.score - a.score);
    mainGenres.sort((a, b) => b.score - a.score);
    secondaryGenres.sort((a, b) => b.score - a.score);

    if (spanImageName) {
      spanImageName.textContent = entry.display_name || imageKey;
    }

    if (spanMainGenres) {
      if (mainGenres.length === 0) {
        spanMainGenres.textContent = "–";
      } else {
        spanMainGenres.textContent = mainGenres
          .map(g => `${g.genre} (${g.score.toFixed(2)})`)
          .join(", ");
      }
    }

    if (spanSecondaryGenres) {
      if (secondaryGenres.length === 0) {
        spanSecondaryGenres.textContent = "–";
      } else {
        spanSecondaryGenres.textContent = secondaryGenres
          .map(g => `${g.genre} (${g.score.toFixed(2)})`)
          .join(", ");
      }
    }

    if (tableResults) {
      tableResults.innerHTML = "";
      if (allRows.length === 0) {
        resetResultsPlaceholder();
        return;
      }
      allRows.forEach(row => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${row.genre}</td>
          <td>${row.score.toFixed(3)}</td>
          <td>${row.type}</td>
        `;
        tableResults.appendChild(tr);
      });
    }
  }

  btnPredict?.addEventListener("click", async () => {
    if (!statusPredict) return;

    const imagePath = ImageStore.getCurrent();
    if (!imagePath) {
      statusPredict.textContent = "Statut : aucune image sélectionnée.";
      statusPredict.classList.add("log-error");
      return;
    }

    const seuilPrincipal  = parseFloat(inputSeuilPrincipal?.value ?? "0.5");
    const seuilSecondaire = parseFloat(inputSeuilSecondaire?.value ?? "0.3");

    if (!Number.isFinite(seuilPrincipal) || seuilPrincipal < 0 || seuilPrincipal > 1) {
      statusPredict.textContent = "Statut : seuil principal invalide.";
      statusPredict.classList.add("log-error");
      return;
    }
    if (!Number.isFinite(seuilSecondaire) || seuilSecondaire < 0 || seuilSecondaire > 1) {
      statusPredict.textContent = "Statut : seuil secondaire invalide.";
      statusPredict.classList.add("log-error");
      return;
    }

    const usePer = !!(checkUsePerClass && checkUsePerClass.checked);

    statusPredict.textContent = "Statut : prédiction en cours…";
    statusPredict.classList.remove("log-error", "log-success");

    const json = await callApi("/api/predict_ivt",{ use_per_class: usePer },statusPredict);

    if (!json || !json.ok) {
      statusPredict.textContent = json?.error || "Statut : erreur de prédiction.";
      statusPredict.classList.add("log-error");
      lastScoresByImage = {};
      lastPerClassThresholds = null;
      resetResultsPlaceholder();
      return;
    }

    console.log(json);

    const preds           = json.predictions || json.preds || json.pred || [];
    const seuilsOptimaux  = json.seuil_optimaux || json.seuils_optimaux || null;

    lastScoresByImage        = {};
    lastPerClassThresholds   = seuilsOptimaux || null;

    if (Array.isArray(preds)) {
      preds.forEach(item => {
        const imgName     = String(item.image);
          const scores      = item.scores || {};
          const displayName = imgName;

          lastScoresByImage[imgName] = {
            scores,
            display_name: displayName
          };
      });
    }

    statusPredict.textContent = "Statut : prédiction terminée.";
    statusPredict.classList.add("log-success");

    updateTolLabel();
    rerecalcFromCache();
  });

  // slider de tolérance
  sliderTol?.addEventListener("input", () => {
    updateTolLabel();
    rerecalcFromCache();
  });

  btnPrev?.addEventListener("click", () => {
      ImageStore.prev();
      updatePreview();
      updateTolLabel();
      rerecalcFromCache();
  });
  btnNext?.addEventListener("click", () => {
      ImageStore.next();
      updatePreview();
      updateTolLabel();
      rerecalcFromCache();
  });

  // init
  updateTolLabel();
  resetResultsPlaceholder();
});
