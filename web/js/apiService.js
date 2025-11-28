export async function callApi(url, payload = {}, logElem = null) {
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    console.log("API", url, data);

    if (logElem) {
      if (res.ok && data.ok) {
        logElem.textContent = data.message || "OK";
        logElem.classList.remove("log-error");
        logElem.classList.add("log-success");
      } else {
        logElem.textContent = data.error || res.statusText || "Erreur inconnue";
        logElem.classList.remove("log-success");
        logElem.classList.add("log-error");
      }
    }

    return data;
  } catch (err) {
    console.error("Erreur callApi:", err);
    if (logElem) {
      logElem.textContent = "Erreur réseau / serveur.";
      logElem.classList.remove("log-success");
      logElem.classList.add("log-error");
    }
    return { ok: false, error: "network_error" };
  }
}
