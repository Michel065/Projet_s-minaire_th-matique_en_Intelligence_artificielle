// web/js/entrainement_ivt4.js
import { callApi } from "./apiService.js";

document.addEventListener("DOMContentLoaded", () => {
  const inputEpochs     = document.getElementById("epochs");
  const inputBatchSize  = document.getElementById("batch-size");
  const inputModelDir   = document.getElementById("model-dir");
  const inputModelName  = document.getElementById("model-name");
  const checkUseBoost   = document.getElementById("use-boost");

  const btnGenDatasets  = document.getElementById("btn-gen-datasets"); 
  const btnTrain        = document.getElementById("btn-train");
  const btnGenGraphs    = document.getElementById("btn-gen-graphs");

  const statusTrain     = document.getElementById("status-train");
  const statusGraphs    = document.getElementById("status-graphs");

  //Préparer les datasets
  btnGenDatasets?.addEventListener("click", async () => {
    const batchSize = parseInt(inputBatchSize?.value ?? "64", 10);
    const useBoost  = !!(checkUseBoost && checkUseBoost.checked);

    if (isNaN(batchSize) || batchSize <= 0) {
      statusTrain.textContent = "Statut : batch size invalide.";
      statusTrain.classList.add("log-error");
      return;
    }

    statusTrain.textContent = "Statut : préparation des datasets…";
    statusTrain.classList.remove("log-error", "log-success");

    const json = await callApi(
      "/api/gen_datasets",
      { batch_size: batchSize, boost: useBoost },
      statusTrain
    );

    if (json && json.ok) {
      statusTrain.textContent = json.message || "Statut : datasets prêts.";
      statusTrain.classList.add("log-success");
    }
  });

  //Lancer l'entraînement
  btnTrain?.addEventListener("click", async () => {
    const epochs    = parseInt(inputEpochs?.value ?? "50", 10);
    const batchSize = parseInt(inputBatchSize?.value ?? "64", 10);
    const modelDir  = (inputModelDir?.value || "").trim();
    const modelName = (inputModelName?.value || "").trim() || "model_poster_vers_theme";
    const useBoost  = !!(checkUseBoost && checkUseBoost.checked);

    if (isNaN(epochs) || epochs <= 0) {
      statusTrain.textContent = "Statut : nombre d'epochs invalide.";
      statusTrain.classList.add("log-error");
      return;
    }
    if (isNaN(batchSize) || batchSize <= 0) {
      statusTrain.textContent = "Statut : batch size invalide.";
      statusTrain.classList.add("log-error");
      return;
    }
    if (!modelDir) {
      statusTrain.textContent = "Statut : dossier de sauvegarde du modèle manquant.";
      statusTrain.classList.add("log-error");
      return;
    }

    statusTrain.textContent = "Statut : entraînement en cours…";
    statusTrain.classList.remove("log-error", "log-success");

    try {
        startTrainStatusLoop(statusTrain);
        const json = await callApi("/api/train",{EPOCHS: epochs,batch_size: batchSize,boost: useBoost,model_dir: modelDir,model_name: modelName},statusTrain);
        if (json && json.ok) {
            statusTrain.textContent = json.message || "Statut : entraînement terminé.";
            statusTrain.classList.add("log-success");
        } else if (json && !json.ok) {
            statusTrain.classList.add("log-error");
        }
    }
    finally {
        stopTrainStatusLoop();
    }
  });

  // Générer les courbes à partir de l'historique 
  btnGenGraphs?.addEventListener("click", async () => {
    const modelDir  = (inputModelDir?.value || "").trim();

    if (!modelDir) {
      statusGraphs.textContent = "Statut : dossier de sauvegarde du modèle manquant.";
      statusGraphs.classList.add("log-error");
      return;
    }

    statusGraphs.textContent = "Statut : génération des courbes en cours…";
    statusGraphs.classList.remove("log-error", "log-success");

    const json = await callApi("/api/generate_graphs",{model_dir: modelDir},statusGraphs);
    if (json && json.ok) {
      const outPaths = json.output_paths || "";
      statusGraphs.textContent = outPaths? `Statut : courbes générées (${outPaths}).`: "Statut : courbes générées.";
      statusGraphs.classList.add("log-success");
    }
  });
});






let intervalTrainStatus = null;

function startTrainStatusLoop(statusElem) {
  if (intervalTrainStatus) return;

  intervalTrainStatus = setInterval(async () => {
    try {
      const res = await fetch("/api/train_status");
      if (!res.ok) return; 

      const json = await res.json();
      if (!json.ok || !json.status) return;

      const st = json.status;
      const epoch        = st.epoch ?? 0;
      const totalEpochs  = st.total ?? null;
      let   percent      = st.percent;

      let msg = `Statut : entraînement en cours… ${percent}%`;
      if (totalEpochs != null) {
        msg += ` (epoch ${epoch + 1}/${totalEpochs})`;
      }
      /*
      if (st.logs && typeof st.logs.loss === "number") {
        msg += ` – loss=${st.logs.loss.toFixed(4)}`;
      }
      */

      statusElem.textContent = msg;
      if (percent >= 100) {
        stopTrainStatusLoop();
      }
    } catch (err) {
      console.error("Erreur train_status:", err);
    }
  }, 3000);
}

function stopTrainStatusLoop() {
  if (intervalTrainStatus) {
    clearInterval(intervalTrainStatus);
    intervalTrainStatus = null;
  }
}
