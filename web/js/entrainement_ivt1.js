import { callApi } from "./apiService.js";

// Initialisation des listeners une fois le DOM chargé
document.addEventListener("DOMContentLoaded", () => {

  const inputDirBoost = document.getElementById("img-dir-boost");
  const inputModelDir = document.getElementById("model-dir");

  const btnBuildFilter = document.getElementById("btnBuildFilter");
  const btnCleanAll    = document.getElementById("btnCleanAll");
  const logData        = document.getElementById("log-data");

//bloc 1:
//1) create data_filtrer.json
  if (btnBuildFilter) {
    btnBuildFilter.addEventListener("click", async () => {
      btnBuildFilter.disabled = true;
      if (logData) {
        logData.textContent = "Construction de data_filtrer.json en cours...";
        logData.classList.remove("log-error", "log-success");
      }

      await callApi("/api/construction_filter_json", {}, logData);

      btnBuildFilter.disabled = false;
    });
  }

  // 2) Clean 
  if (btnCleanAll) {
    btnCleanAll.addEventListener("click", async () => {

      const dirBoost = (inputDirBoost?.value || "").trim();
      const dirMODEL = (inputModelDir?.value || "").trim();

      if (!dirBoost) {
        if (logData) {
          logData.textContent = "Erreur : dossier d’augmentation non renseigné.";
          logData.classList.add("log-error");
        }
        return;
      }

      if (!confirm(`Tu es sûr ? Ça va supprimer data_filtrer.json et tout le contenu de :\n${dirBoost} et ${dirMODEL}`)) {
        return;
      }

      btnCleanAll.disabled = true;

      if (logData) {
        logData.textContent = "Nettoyage en cours...";
        logData.classList.remove("log-error", "log-success");
      }

      const json = await callApi("/api/clean",{ img_dir_boost: dirBoost,"model_dir":dirMODEL },logData);

      btnCleanAll.disabled = false;
    });
  }
});
