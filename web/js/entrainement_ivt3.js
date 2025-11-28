import { callApi } from "./apiService.js";

document.addEventListener("DOMContentLoaded", () => {
  const inputRatioVal  = document.getElementById("ratio-val");
  const inputRatioTest = document.getElementById("ratio-test");
  const inputMaxVar    = document.getElementById("max-var");
  const inputFacteur   = document.getElementById("facteur-cible");
  const inputDirBoost = document.getElementById("img-dir-boost");

  const statusSplit    = document.getElementById("status-split-boost");
  const btnSplit       = document.getElementById("btn-split");
  const btnBoost       = document.getElementById("btn-boost");

  // Split Train / Val / Test
  btnSplit?.addEventListener("click", async () => {
    // On récupère en % dans le formulaire → on convertit en ratio
    const valPct  = parseFloat(inputRatioVal?.value ?? "15");
    const testPct = parseFloat(inputRatioTest?.value ?? "15");

    if (
      isNaN(valPct)  || isNaN(testPct) ||
      valPct < 0     || testPct < 0    ||
      valPct + testPct >= 100
    ) {
      statusSplit.textContent = "Statut : ratios invalides (la somme doit être < 100%).";
      statusSplit.classList.add("log-error");
      return;
    }

    const ratioVal  = valPct  / 100.0;
    const ratioTest = testPct / 100.0;

    statusSplit.textContent = "Statut : split en cours…";
    statusSplit.classList.remove("log-error", "log-success");

    const json = await callApi(
      "/api/split_train_val_test",
      {
        ratio_val:  ratioVal,
        ratio_test: ratioTest,
      },
      statusSplit
    );

    if (json && json.ok && Array.isArray(json.data)) {
      const [tTrain, tVal, tTest] = json.data;
      statusSplit.textContent =
        `Statut : Split OK (train=${tTrain}, val=${tVal}, test=${tTest})`;
      statusSplit.classList.add("log-success");
    }
  });

  // Boost sur le TRAIN
  btnBoost?.addEventListener("click", async () => {
    const maxVar   = parseInt(inputMaxVar?.value ?? "15", 10);
    const facteur  = parseFloat(inputFacteur?.value ?? "0.5");
    const dirBoost = (inputDirBoost?.value || "").trim();

    if (!dirBoost) {
      statusSplit.textContent = "Statut : dossier d’augmentation invalide.";
      statusSplit.classList.add("log-error");
      return;
    }

    if (isNaN(maxVar) || maxVar <= 0) {
      statusSplit.textContent = "Statut : max variantes invalide.";
      statusSplit.classList.add("log-error");
      return;
    }

    if (isNaN(facteur) || facteur <= 0) {
      statusSplit.textContent = "Statut : facteur cible invalide.";
      statusSplit.classList.add("log-error");
      return;
    }

    statusSplit.textContent = "Statut : boost en cours…";
    statusSplit.classList.remove("log-error", "log-success");

    const json = await callApi("/api/boost_train",{img_dir_boost: dirBoost,max_variantes_par_image: maxVar,facteur_cible: facteur},statusSplit);

    if (json && json.ok) {
      const n = json.nbr_ajout ?? 0;
      statusSplit.textContent =
        `Statut : boost terminé – ${n} posters ajoutés pour le train.`;
      statusSplit.classList.add("log-success");
    }
  });
});
