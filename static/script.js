const BASE_URL = "https://yt-backend-sz4a.onrender.com";

async function fetchInfo() {

    const url = document.getElementById("urlInput").value.trim();

    if (!url) {
        alert("Paste URL");
        return;
    }

    document.getElementById("loading").classList.remove("hidden");

    try {

        const res = await fetch(BASE_URL + "/info", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ url })
        });

        const data = await res.json();

        console.log(data); // DEBUG

        if (data.error) {
            alert(data.error);
            return;
        }

        document.getElementById("thumbnail").src = data.thumbnail;
        document.getElementById("title").innerText = data.title;

        const videoList = document.getElementById("videoList");
        videoList.innerHTML = "";

        data.videos.forEach(v => {
            const btn = document.createElement("button");
            btn.innerText = v.resolution + "p";
            btn.onclick = () => download(v.format_id, "video");
            videoList.appendChild(btn);
        });

        document.getElementById("loading").classList.add("hidden");
        document.getElementById("content").classList.remove("hidden");

    } catch (e) {
        alert("Backend sleeping. Wait 10s and try again.");
    }
}


async function download(format_id, type) {

    const url = document.getElementById("urlInput").value;

    const res = await fetch(BASE_URL + "/download", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ url, format_id, type })
    });

    const data = await res.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    window.location = BASE_URL + "/file?path=" + data.file;
}