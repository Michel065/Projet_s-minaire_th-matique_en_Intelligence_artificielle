import { callApi } from "./apiService.js";

document.addEventListener("DOMContentLoaded", () => {
  const inputModelDir  = document.getElementById("model-dir-test");
  const inputModelName = document.getElementById("model-name-test");
  const btnLoadModel   = document.getElementById("btn-load-model");
  const statusModel    = document.getElementById("status-model");

  btnLoadModel?.addEventListener("click", async () => {
    const modelDir  = (inputModelDir?.value || "").trim();
    const modelName = (inputModelName?.value || "").trim() || "model_pvt";

    if (!modelDir) {
      statusModel.textContent = "Statut : dossier du modèle manquant.";
      statusModel.classList.remove("log-success");
      statusModel.classList.add("log-error");
      return;
    }
    
    if (!modelName) {
      statusModel.textContent = "Statut : nom du modèle manquant.";
      statusModel.classList.remove("log-success");
      statusModel.classList.add("log-error");
      return;
    }

    statusModel.textContent = "Statut : chargement du modèle…";
    statusModel.classList.remove("log-error", "log-success");

    const json = await callApi("/api/load_model",{model_dir: modelDir,model_name: modelName,},statusModel);

    if (json && json.ok) {
      statusModel.textContent = "Statut : modèle chargé.";
      statusModel.classList.remove("log-error");
      statusModel.classList.add("log-success");
    }
  });
});
