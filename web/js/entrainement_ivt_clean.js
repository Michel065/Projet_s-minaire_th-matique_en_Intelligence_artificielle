import { callApi } from "./apiService.js";

document.addEventListener("DOMContentLoaded", () => {
  const btnCleanFilter = document.getElementById("btnCleanFilter");
  const btnCleanBoost  = document.getElementById("btnCleanBoost");
  const btnCleanModel  = document.getElementById("btnCleanModel");
  const btnCleanAll    = document.getElementById("btnCleanAll");

  const statusClean    = document.getElementById("clean-status");

  const inputBoostDir  = document.getElementById("img-dir-boost");
  const inputModelDir  = document.getElementById("model-dir");

  function setStatus(msg, isError = false) {
    if (!statusClean) return;
    statusClean.textContent = msg;
    statusClean.classList.remove("log-error", "log-success");
    if (isError) {
      statusClean.classList.add("log-error");
    }
  }

  //Clean data_filtrer.json
  btnCleanFilter?.addEventListener("click", async () => {
    if (!confirm("Supprimer uniquement data_filtrer.json ?")) return;

    setStatus("Nettoyage de data_filtrer.json en cours...");

    await callApi("/api/clean_filter", {}, statusClean );
  });

  //Clean dossier d’augmentation
  btnCleanBoost?.addEventListener("click", async () => {
    const dirBoost = (inputBoostDir?.value || "").trim();

    if (!confirm(`Supprimer le dossier d’augmentation (${dirBoost || "par défaut"}) ?`))
      return;

    setStatus("Nettoyage du dossier d’augmentation en cours...");
    await callApi("/api/clean_boost",{ img_dir_boost: dirBoost || undefined },statusClean );
  });

  //Clean dossier du modèle
  btnCleanModel?.addEventListener("click", async () => {
    const modelDir = (inputModelDir?.value || "").trim();

    if (!confirm(`Supprimer le contenu du dossier modèle (${modelDir || "par défaut"}) ?`))
      return;

    setStatus("Nettoyage du dossier du modèle en cours...");

    await callApi("/api/clean_model",{ model_dir: modelDir || undefined },statusClean );
  });

  //Clean ALL
  btnCleanAll?.addEventListener("click", async () => {
    const dirBoost = (inputBoostDir?.value || "").trim();
    const modelDir = (inputModelDir?.value || "").trim();

    if (!confirm("Tout nettoyer (data_filter + augmentation + modèle) ?")) return;
    setStatus("Nettoyage complet en cours...");

    await callApi("/api/clean_all",{img_dir_boost: dirBoost,model_dir: modelDir},statusClean );
  });
});
