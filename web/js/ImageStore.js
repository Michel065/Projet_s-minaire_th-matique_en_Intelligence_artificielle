export class ImageStore {
    static images = [];       
    static currentIndex = 0; 

    static setImages(list) {
        this.images = list;
        this.currentIndex = 0;
    }

    static getCurrent() {
        return this.images[this.currentIndex] || null;
    }

    static getName() {
        if (!this.images || this.images.length === 0) {
            return "Image 0 / 0";
        }
        return `Image ${this.currentIndex + 1} / ${this.images.length}`;
    }

    static getName_mais_bien() {
        const path = this.getCurrent();
        if (!path) return null;
        const base = path.split(/[\\/]/).pop();   // "399_boost_1.jpg"
        return base.replace(/\.[^.]+$/, "");      // "399_boost_1"
    }

    static next() {
        if (this.images.length === 0) return null;
        this.currentIndex = (this.currentIndex + 1) % this.images.length;
        return this.getCurrent();
    }

    static prev() {
        if (this.images.length === 0) return null;
        this.currentIndex =
            (this.currentIndex - 1 + this.images.length) % this.images.length;
        return this.getCurrent();
    }
}

export function updatePreview() {
    const zone   = document.getElementById("preview-zone");
    const label  = document.getElementById("label-current-image");
    zone.innerHTML = "";

    const image = ImageStore.getCurrent();

    // Aucun résultat
    if (!image) {
        zone.innerHTML = `<span class="image-placeholder">Aucune image sélectionnée.</span>`;
        label.textContent = "Image 0 / 0";
        return;
    }

    console.log(image);
    const img = document.createElement("img");
    img.src = image;
    img.style.maxWidth = "100%";
    img.style.maxHeight = "100%";
    img.style.objectFit = "contain";

    zone.appendChild(img);
    label.textContent = ImageStore.getName();
}
