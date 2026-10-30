.pragma library

// Hardware descriptions checked against Sennheiser's HDB 630 manual and FAQ.
var topics = {
    graphic: {title:"Five-band graphic EQ", body:"Adjust bass through treble at five fixed frequencies. Values run from −6 to +6 dB. Choosing a built-in preset fills the draft; Apply writes all five bands and switches the headphones to Graphic EQ. Parametric EQ is a separate processing mode."},
    broadcast: {title:"Auracast broadcast", body:"Send one audio stream to compatible Auracast receivers. Read settings, choose the broadcast name, visibility, quality and optional password, then Save. Broadcast audio mode starts transmission separately. A blank password keeps an existing one; passwords are never shown or saved on this computer."},
    anti_wind: {title:"Reduce wind rumble", body:"Automatic adjusts wind-noise reduction as needed. Maximum favors stronger reduction. Off disables this wind-specific feature; it does not turn off all ANC."},
    sidetone: {title:"Call transparency / sidetone", body:"Controls how much of your own voice you hear during calls. Off disables it; levels 1–4 increase the amount. This differs from the ambient transparency balance used for music."},
    auto_pause: {title:"Pause for call transparency", body:"Pauses playback when call transparency / sidetone is activated, instead of continuing to mix music. Headphone firmware and the calling app determine the final behavior."},
    auto_off: {title:"Automatic power off", body:"Turns the headphones off after the selected idle period. Never disables the timer. The headphones may disable this dependent feature when on-head detection is off."},
    resolution: {title:"Wireless resolution preference", body:"High resolution allows compatible links to negotiate up to 24-bit / 96 kHz. Standard favors compatibility. The stream and source still determine actual quality. Changing this preference requires a headphone restart."},
    presets: {title:"Local parametric EQ library", body:"Save a draft under a name on this computer. Loading a preset edits the form only; Save EQ to headphones applies it. Saving an existing name replaces it. Deleting a preset removes the local copy, leaving the headphone tuning unchanged."},
    bass_boost: {title:"Bass boost", body:"Adds the headphone firmware's bass emphasis where supported by the current audio mode. Speech processing can override EQ and bass boost."},
    headphone_audio_mode: {title:"Audio processing mode", body:"Original sound disables EQ processing. Graphic EQ uses the headphone's stored five-band graphic settings. Speech / podcast emphasizes spoken content and can override EQ or bass boost. Parametric EQ uses the five detailed stages edited below."},
    audio_mode: {title: "Audio mode", body: "High quality prioritizes music. Low latency reduces sound delay for games and video. Broadcast sends Auracast audio to compatible receivers; configure its name and password below."},
    transport: {title: "Bluetooth connection type", body: "Classic uses codecs such as aptX Adaptive. LE Audio uses LC3 with compatible receivers. Multipoint is the dongle's additional connection mode; available behavior depends on the receiver."},
    codec: {title: "How wireless audio travels", body: "A codec encodes sound for Bluetooth. Automatic allows the codecs the dongle reports. A specific choice restricts negotiation; the headphones must support it too. The active codec is shown above."},
    connection: {title: "Why another Bluetooth connection?", body: "The dongle carries audio. A direct computer-to-headphones connection carries settings. Both can stay connected, using the two headphone multipoint slots."},
    anc: {title: "Noise cancellation", body: "Uses microphones to reduce surrounding noise. This enables the noise-control system, including its manual transparency balance. It does not change music volume."},
    adaptive: {title: "Adaptive ANC", body: "Automatically adjusts noise cancellation to your surroundings. Turn it off to choose a manual transparency balance."},
    comfort: {title: "Comfort ANC · experimental", body: "The firmware exposes this flag, but its audible effect is undocumented. It is separate from Comfort Call."},
    transparency: {title: "Quiet surroundings ↔ hear the room", body: "Left favors noise cancellation. Right lets more outside sound through the microphones. For manual adjustment, enable Noise cancellation and turn Adaptive ANC off. Changes apply on release.", visual: "transparency"},
    crossfeed: {title: "A more speaker-like stereo image", body: "Blends a little of each channel into the opposite ear. Low is subtle; High blends more. Off keeps the original stereo separation.", visual: "crossfeed"},
    on_head: {title: "On-head detection", body: "Detects whether you are wearing the headphones. Smart pause and wear-triggered call features depend on this sensor."},
    smart_pause: {title: "Smart pause", body: "Pauses music when you remove the headphones and resumes when you put them back on. Requires on-head detection and player support."},
    auto_answer: {title: "Auto-answer calls", body: "Answers an incoming call when you put on the headphones. Requires on-head detection; support depends on the calling app."},
    comfort_call: {title: "Hear yourself during calls", body: "Plays your own voice back into the headphones during calls, making speaking feel more natural."},
    eq: {title: "Shape the sound", body: "Each EQ band changes part of the sound. Frequency chooses where, gain chooses how much, and Q sets the width. Read first, edit, Save, then Enable parametric EQ.", visual: "eq"},
    pregain: {title: "Leave room for EQ boosts", body: "Lowers the signal before EQ. Negative pre-gain leaves room for boosted bands and helps avoid digital clipping. This control cuts from 0 to −12 dB."},
    filter: {title: "Choose the shape of a band", body: "Bell targets a frequency region. Low/high shelves affect bass/treble. Low/high-pass filters cut above/below the cutoff; second-order filters are steeper. Tilt balances bass against treble. All-pass changes phase. Gain adjusts level; Bypass skips the band."},
    frequency: {title: "Frequency · Hz", body: "Chooses where the filter acts: low values affect bass, middle values affect much of the voice range, and high values affect treble. The diagram is a general guide.", visual: "eq"},
    gain: {title: "Gain · dB", body: "Positive values boost; negative values cut. Start with small changes and compare at similar loudness. Gain has different effects depending on the selected filter."},
    q: {title: "Q · width of the adjustment", body: "For a bell filter, low Q changes a broad range; high Q targets a narrower range. Shelves require Q from 0.25 to 0.71; other supported filters allow up to 8.", visual: "eq"}
}
function get(key) { return topics[key] || {title: "Setting", body: ""} }
