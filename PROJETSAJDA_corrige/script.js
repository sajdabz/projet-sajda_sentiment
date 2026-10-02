const API = "http://127.0.0.1:8000";

let modeActif = "texte";   // "texte" | "camera" | "les-deux"
let streamCamera = null;
let photoData = null;      // data URL de la photo capturée

/* ---------- utilitaires ---------- */

async function appelerAPI(route, corps) {
    const response = await fetch(API + route, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(corps)
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(typeof data.detail === "string" ? data.detail : "Erreur du serveur");
    }
    return data;
}

// positif => +score, négatif => -score, neutre => 0
function scoreSigne(r) {
    if (r.sentiment === "positif") return r.score;
    if (r.sentiment === "négatif") return -r.score;
    return 0;
}

function afficherJauge(sentiment, valeurSignee, confiance, detail) {
    document.getElementById("gaugeNeedle").style.transform =
        "rotate(" + (valeurSignee * 90) + "deg)";

    const t = document.getElementById("texteSentiment");
    t.innerText = sentiment;
    t.className = sentiment;
    document.getElementById("texteScore").innerText =
        "Confiance : " + Math.round(confiance * 100) + "%";
    document.getElementById("detailResultat").innerText = detail || "";
    document.getElementById("resultat").style.display = "block";
}

/* ---------- caméra ---------- */

async function ouvrirCamera() {
    try {
        streamCamera = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "user" }
        });
        const video = document.getElementById("video");
        video.srcObject = streamCamera;
        video.style.display = "block";
        document.getElementById("photoPrise").style.display = "none";
        document.getElementById("btnOuvrirCamera").style.display = "none";
        document.getElementById("btnCapturer").style.display = "inline-block";
        document.getElementById("btnReprendre").style.display = "none";
    } catch (error) {
        alert("Impossible d'accéder à la caméra : " + error.message);
    }
}

function arreterCamera() {
    if (streamCamera) {
        streamCamera.getTracks().forEach(t => t.stop());
        streamCamera = null;
    }
}

function capturerPhoto() {
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");
    if (!video.videoWidth) { alert("La caméra n'est pas encore prête."); return; }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);

    // JPEG : beaucoup plus léger que PNG pour l'envoi
    photoData = canvas.toDataURL("image/jpeg", 0.9);

    const photo = document.getElementById("photoPrise");
    photo.src = photoData;
    photo.style.display = "block";
    video.style.display = "none";
    arreterCamera();

    document.getElementById("btnCapturer").style.display = "none";
    document.getElementById("btnReprendre").style.display = "inline-block";
}

function reprendrePhoto() {
    photoData = null;
    ouvrirCamera();
}

/* ---------- modes ---------- */

function basculerMode(mode) {
    modeActif = mode;
    const avecTexte = (mode === "texte" || mode === "les-deux");
    const avecPhoto = (mode === "camera" || mode === "les-deux");

    document.getElementById("zoneTexte").style.display = avecTexte ? "block" : "none";
    document.getElementById("zoneCamera").style.display = avecPhoto ? "block" : "none";

    const boutons = { "texte": "btnModeTexte", "camera": "btnModeCamera", "les-deux": "btnModeLesDeux" };
    for (const [m, id] of Object.entries(boutons)) {
        const b = document.getElementById(id);
        b.classList.toggle("btn-primary", m === mode);
        b.classList.toggle("btn-outline-secondary", m !== mode);
    }
    if (!avecPhoto) arreterCamera();
    document.getElementById("resultat").style.display = "none";
}

/* ---------- analyse ---------- */

async function analyserTexte() {
    const texte = document.getElementById("Analyse").value.trim();
    if (!texte) throw new Error("Écris un texte avant d'analyser !");
    return appelerAPI("/analyze", { texte });
}

async function analyserVisage() {
    if (!photoData) throw new Error("Ouvre la caméra et capture une photo d'abord !");
    return appelerAPI("/analyze-face", { image: photoData });
}

async function analyser() {
    const btn = document.getElementById("btnAnalyser");
    btn.disabled = true;
    btn.innerText = "Analyse en cours...";

    try {
        if (modeActif === "texte") {
            const r = await analyserTexte();
            afficherJauge(r.sentiment, scoreSigne(r), r.score, "Analyse du texte");

        } else if (modeActif === "camera") {
            const r = await analyserVisage();
            afficherJauge(r.sentiment, scoreSigne(r), r.score,
                "Émotion détectée sur le visage : " + r.emotion_dominante);

        } else {
            // texte + photo : on combine les deux résultats
            const [rt, rv] = await Promise.all([analyserTexte(), analyserVisage()]);
            const moyenne = (scoreSigne(rt) + scoreSigne(rv)) / 2;
            const sentiment = moyenne > 0.15 ? "positif" : moyenne < -0.15 ? "négatif" : "neutre";
            afficherJauge(sentiment, moyenne, Math.abs(moyenne),
                "Texte : " + rt.sentiment + " | Visage : " + rv.sentiment +
                " (" + rv.emotion_dominante + ")");
        }
    } catch (error) {
        alert(error.message.includes("fetch")
            ? "Erreur : impossible de contacter le serveur."
            : error.message);
        console.error(error);
    } finally {
        btn.disabled = false;
        btn.innerText = "Analyser";
    }
}
