setTimeout(() => {
    window.editor = ace.edit("editor");
    window.editor.setTheme("ace/theme/chaos");
    window.editor.session.setMode("ace/mode/yaml");
}, 0);

// Lmao this code sucks
function updateConfig() {
    let currentValue = window.editor.getValue();
    fetch(`/guilds/${window.tags.guild_id}/bot/${window.tags.bot_id}/update`, {method: "POST", body: currentValue}).then((resp) => {
        if (resp.status !== 200) resp.text().then((text) => alert(`Save failed. ${text}`))
    })
}