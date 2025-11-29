import { callApi } from "./apiService.js";
import { ImageStore , updatePreview } from "./ImageStore.js";

document.addEventListener("DOMContentLoaded", () => {
  const radiosMode     = document.querySelectorAll("input[name='mode-image']");
  const fieldSingle    = document.getElementById("field-single-path");
  const fieldFolder    = document.getElementById("field-folder-path");
  const fieldFolderNb  = document.getElementById("field-folder-nb");

  const inputSingle    = document.getElementById("image-path");
  const inputFolder    = document.getElementById("folder-path");
  const inputNbRand    = document.getElementById("nb-random");

  const btnLoadImages  = document.getElementById("btn-load-images");
  const statusImages   = document.getElementById("status-images");

  //Changement mode
  radiosMode.forEach(radio => {
    radio.addEventListener("change", () => {
      const mode = document.querySelector("input[name='mode-image']:checked")?.value;

      if (mode === "single") {
        fieldSingle.style.display = "flex";
        fieldFolder.style.display = "none";
        fieldFolderNb.style.display = "none";
      } else {
        fieldSingle.style.display = "none";
        fieldFolder.style.display = "flex";
        fieldFolderNb.style.display = "flex";
      }
    });
  });

  //Load images
  btnLoadImages?.addEventListener("click", async () => {

    const mode = document.querySelector("input[name='mode-image']:checked")?.value;

    if (!mode) return;

    statusImages.textContent = "Statut : chargement...";
    statusImages.classList.remove("log-error", "log-success");

    let payload = {};

    if (mode === "single") {
      const path = (inputSingle?.value || "").trim();

      if (!path) {
        statusImages.textContent = "Erreur : chemin de l'image manquant.";
        statusImages.classList.add("log-error");
        return;
      }

      payload = {
        mode: "single",
        image_path: path
      };
    }

    else if (mode === "folder") {
      const folder = (inputFolder?.value || "").trim();
      const nb = Number(inputNbRand?.value || 1);

      if (!folder) {
        statusImages.textContent = "Erreur : dossier manquant.";
        statusImages.classList.add("log-error");
        return;
      }

      payload = {
        mode: "folder",
        folder_path: folder,
        nb_random: nb
      };
    }

    const json = await callApi("/api/load_images_test", payload, statusImages);

    if (!json || !json.ok) {
      statusImages.textContent = "Erreur : impossible de charger le(s) image(s).";
      statusImages.classList.add("log-error");
      ImageStore.setImages([]);
      updatePreview();
      return;
    }
    //./MoviePostersAugmentation/399_boost_1.jpg
    const images = json.images || [];
    console.log(images)
    if (images.length > 0) {
        statusImages.textContent = `Statut : ${images.length} image(s) chargée(s).`;
        statusImages.classList.add("log-success");
    } else {
        statusImages.textContent = "Statut : aucune image trouvée.";
        statusImages.classList.add("log-error");
    }
    ImageStore.setImages(images);
    updatePreview();
  });
});
