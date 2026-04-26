const BASE_URL = "https://yt-backend-sz4a.onrender.com";
/* ===========================
   GLOBAL STATE
=========================== */

let currentURL = "";
let videoFormats = [];
let audioFormats = [];
let activeTab = "video";

const loadingEl = document.getElementById("loading");
const contentEl = document.getElementById("content");
const progressSection = document.getElementById("progressSection");

const videoList = document.getElementById("videoList");
const audioList = document.getElementById("audioList");

const progressFill = document.getElementById("progressFill");
const statusText = document.getElementById("statusText");


/* ===========================
   FETCH VIDEO INFO
=========================== */

async function fetchInfo() {

    const url = document.getElementById("urlInput").value.trim();

    if (!url) {
        alert("Paste a YouTube URL first");
        return;
    }

    currentURL = url;

    showLoading(true);
    contentEl.classList.add("hidden");

    try {

        const res = await fetch(BASE_URL + "/info", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ url })
        });

        const data = await res.json();

        populatePreview(data);
        buildQualityLists(data);

        showLoading(false);
        contentEl.classList.remove("hidden");

    } catch (err) {
        console.error(err);
        alert("Failed to fetch video info.");
        showLoading(false);
    }
}


/* ===========================
   LOADING STATE
=========================== */

function showLoading(state){
    if(state){
        loadingEl.classList.remove("hidden");
    } else {
        loadingEl.classList.add("hidden");
    }
}


/* ===========================
   PREVIEW SECTION
=========================== */

function populatePreview(data){

    document.getElementById("thumbnail").src = data.thumbnail;
    document.getElementById("title").innerText = data.title;

    videoFormats = data.videos;
    audioFormats = data.audios;
}


/* ===========================
   BUILD QUALITY CARDS
=========================== */

function buildQualityLists(data){

    videoList.innerHTML = "";
    audioList.innerHTML = "";

    // VIDEO OPTIONS
    data.videos.forEach(v => {

        const card = createQualityCard({
            title: `${v.resolution}p`,
            meta: `${v.ext.toUpperCase()} • ${v.size}`,
            format_id: v.format_id,
            type: "video"
        });

        videoList.appendChild(card);
    });


    // AUDIO OPTIONS
    data.audios.forEach(a => {

        const card = createQualityCard({
            title: `${Math.round(a.abr || 0)} kbps`,
            meta: `${a.ext.toUpperCase()} • ${a.size}`,
            format_id: a.format_id,
            type: "audio"
        });

        audioList.appendChild(card);
    });
}


/* ===========================
   CREATE CARD COMPONENT
=========================== */

function createQualityCard({title, meta, format_id, type}){

    const card = document.createElement("div");
    card.className = "quality-card";

    const info = document.createElement("div");
    info.className = "quality-info";

    const titleEl = document.createElement("div");
    titleEl.className = "quality-title";
    titleEl.innerText = title;

    const metaEl = document.createElement("div");
    metaEl.className = "quality-meta";
    metaEl.innerText = meta;

    info.appendChild(titleEl);
    info.appendChild(metaEl);

    const btn = document.createElement("button");
    btn.className = "download-btn";
    btn.innerText = "Download";

    btn.onclick = () => startDownload(format_id, type);

    card.appendChild(info);
    card.appendChild(btn);

    return card;
}


/* ===========================
   TAB SWITCHING
=========================== */

function switchTab(tab){

    activeTab = tab;

    document.querySelectorAll(".tab").forEach(t =>
        t.classList.remove("active")
    );

    if(tab === "video"){
        videoList.classList.remove("hidden");
        audioList.classList.add("hidden");
        document.querySelectorAll(".tab")[0].classList.add("active");
    } else {
        audioList.classList.remove("hidden");
        videoList.classList.add("hidden");
        document.querySelectorAll(".tab")[1].classList.add("active");
    }
}


/* ===========================
   DOWNLOAD PROCESS
=========================== */

async function startDownload(format_id, type){

    progressSection.classList.remove("hidden");
    statusText.innerText = "Preparing download...";

    animateProgress();

    try {

        const res = await fetch(BASE_URL + "/download", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                url: currentURL,
                format_id,
                type
            })
        });

        const data = await res.json();

        finishProgress();

        statusText.innerText = "Download ready ✅";

        setTimeout(() => {
            window.location =
                BASE_URL + "/file?path=" + encodeURIComponent(data.file);
        }, 800);

    } catch(err){
        console.error(err);
        statusText.innerText = "Download failed ❌";
    }
}


/* ===========================
   PROGRESS ANIMATION
=========================== */

let progressInterval;

function animateProgress(){

    progressFill.style.width = "0%";

    let progress = 0;

    progressInterval = setInterval(() => {

        progress += Math.random() * 7;

        if(progress >= 90){
            clearInterval(progressInterval);
        }

        progressFill.style.width = progress + "%";

    }, 350);
}


function finishProgress(){
    clearInterval(progressInterval);
    progressFill.style.width = "100%";
}


/* ===========================
   ENTER KEY SUPPORT
=========================== */

document
.getElementById("urlInput")
.addEventListener("keypress", function(e){
    if(e.key === "Enter"){
        fetchInfo();
    }
});