.pragma library

function dependency(key, values) {
    if (key === "bass_boost" && values.audio_mode !== 1)
        return {available:false, reason:"Available in Graphic EQ mode."}
    if (["smart_pause", "auto_answer", "auto_off"].indexOf(key) >= 0 && !values.on_head)
        return {available:false, reason:"Enable On-head detection to use this setting."}
    if (["adaptive", "comfort", "anti_wind"].indexOf(key) >= 0 && !values.anc)
        return {available:false, reason:"Enable Noise cancellation to use this setting."}
    return {available:true, reason:""}
}

function eqStatus(mode, kind) {
    if (mode === kind) return "Active for playback. Edits apply when saved."
    if (mode === 2) return "Inactive while Speech / podcast is selected. You can still prepare a draft."
    if (mode === 0) return "EQ is off. You can still prepare a draft."
    return "Inactive for playback. You can still prepare a draft."
}
