import { callApi } from "./apiService.js";

// Initialisation des listeners une fois le DOM chargé
document.addEventListener("DOMContentLoaded", () => {
  const btnBuildFilter = document.getElementById("btnBuildFilter");
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
});
