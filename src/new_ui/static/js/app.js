/**
 * TTS Timeline Studio - Main Application
 * Supports XTTS v2 and Fish Speech engines
 */

// =============================================================================
// State
// =============================================================================

const state = {
    engines: [],
    currentEngine: 'xtts_v2',
    voices: [],
    languages: [],
    tracks: {},          // { voiceName: { samples: [], muted: false, solo: false } }
    samples: [],         // All samples flat list for reference
    selectedSample: null,
    isPlaying: false,
    playhead: 0,         // Current playhead position in seconds
    playStartTime: 0,    // When playback started
    zoom: 100,           // Pixels per second
    audioContext: null,
    playbackAnimationId: null,
};

// =============================================================================
// DOM Elements
// =============================================================================

const elements = {
    // Generation
    textInput: document.getElementById('textInput'),
    engineSelect: document.getElementById('engineSelect'),
    voiceSelect: document.getElementById('voiceSelect'),
    languageSelect: document.getElementById('languageSelect'),
    generateBtn: document.getElementById('generateBtn'),
    voiceChips: document.getElementById('voiceChips'),
    uploadVoiceBtn: document.getElementById('uploadVoiceBtn'),
    paramsRow: document.getElementById('paramsRow'),

    // XTTS params
    tempSlider: document.getElementById('tempSlider'),
    tempValue: document.getElementById('tempValue'),
    speedSlider: document.getElementById('speedSlider'),
    speedValue: document.getElementById('speedValue'),

    // Fish Speech params
    fishTempSlider: document.getElementById('fishTempSlider'),
    fishTempValue: document.getElementById('fishTempValue'),
    topPSlider: document.getElementById('topPSlider'),
    topPValue: document.getElementById('topPValue'),
    repPenaltySlider: document.getElementById('repPenaltySlider'),
    repPenaltyValue: document.getElementById('repPenaltyValue'),

    // Timeline
    timeline: document.getElementById('timeline'),
    tracksContainer: document.getElementById('tracksContainer'),
    timeRuler: document.getElementById('timeRuler'),
    emptyState: document.getElementById('emptyState'),
    totalDuration: document.getElementById('totalDuration'),
    sampleCount: document.getElementById('sampleCount'),
    zoomSlider: document.getElementById('zoomSlider'),

    // Playhead
    playheadLine: document.getElementById('playheadLine'),
    playheadMarker: document.getElementById('playheadMarker'),
    playheadTime: document.getElementById('playheadTime'),

    // Controls
    playBtn: document.getElementById('playBtn'),
    playIcon: document.getElementById('playIcon'),
    stopBtn: document.getElementById('stopBtn'),
    exportWavBtn: document.getElementById('exportWavBtn'),
    exportZipBtn: document.getElementById('exportZipBtn'),
    exportEdlBtn: document.getElementById('exportEdlBtn'),

    // Status
    statusDot: document.getElementById('statusDot'),
    statusText: document.getElementById('statusText'),

    // Context Menu
    contextMenu: document.getElementById('contextMenu'),
    volumeSlider: document.getElementById('volumeSlider'),
    volumeValue: document.getElementById('volumeValue'),

    // Modals
    uploadModal: document.getElementById('uploadModal'),
    voiceNameInput: document.getElementById('voiceNameInput'),
    voiceFileInput: document.getElementById('voiceFileInput'),
    cancelUploadBtn: document.getElementById('cancelUploadBtn'),
    confirmUploadBtn: document.getElementById('confirmUploadBtn'),

    // Loading
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingText: document.getElementById('loadingText'),

    // Audio
    audioPlayer: document.getElementById('audioPlayer'),
};

// =============================================================================
// API Functions
// =============================================================================

async function fetchEngines() {
    const res = await fetch('/api/engines');
    const data = await res.json();
    state.engines = data.engines;
    state.currentEngine = data.current || 'xtts_v2';
    return data;
}

async function fetchVoices() {
    const res = await fetch('/api/voices');
    const data = await res.json();
    state.voices = data.voices;
    state.languages = data.languages;
    return data;
}

async function selectEngine(engine) {
    const res = await fetch('/api/engines/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ engine })
    });
    if (res.ok) {
        state.currentEngine = engine;
        // Refresh voices/languages for new engine
        await fetchVoices();
        populateLanguageSelect();
    }
    return res.json();
}

async function generateSample(text, voice, engine, language, params) {
    const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice, engine, language, ...params })
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Generation failed');
    }
    return res.json();
}

async function deleteSampleAPI(filename) {
    await fetch(`/api/samples/${filename}`, { method: 'DELETE' });
}

async function fetchWaveform(filename) {
    const res = await fetch(`/api/samples/${filename}/waveform?points=100`);
    if (res.ok) {
        return res.json();
    }
    return null;
}

async function exportTimeline(format) {
    const samples = getAllSamplesForExport();
    const res = await fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ samples, format })
    });
    if (!res.ok) throw new Error('Export failed');

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `export_${Date.now()}.${format === 'edl' ? 'edl' : format === 'zip' ? 'zip' : 'wav'}`;
    a.click();
    URL.revokeObjectURL(url);
}

async function uploadVoice(name, file) {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('file', file);
    const res = await fetch('/api/voices/upload', {
        method: 'POST',
        body: formData
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
}

async function previewVoice(voiceName) {
    elements.audioPlayer.src = `/api/voices/${voiceName}/preview`;
    elements.audioPlayer.play();
}

// =============================================================================
// UI Functions
// =============================================================================

function showLoading(text = 'Chargement...') {
    elements.loadingText.textContent = text;
    elements.loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    elements.loadingOverlay.style.display = 'none';
}

function updateStatus(text, isLoading = false) {
    elements.statusText.textContent = text;
    elements.statusDot.classList.toggle('loading', isLoading);
}

function populateEngineSelect() {
    // Update select options based on available engines
    const options = state.engines.map(e => {
        const available = e.available ? '' : ' (non installé)';
        return `<option value="${e.name}" ${!e.available ? 'disabled' : ''} ${e.name === state.currentEngine ? 'selected' : ''}>${e.name === 'xtts_v2' ? 'XTTS v2' : 'Fish Speech'}${available}</option>`;
    });
    elements.engineSelect.innerHTML = options.join('');
}

function populateVoiceSelect() {
    elements.voiceSelect.innerHTML = state.voices.map(v =>
        `<option value="${v.name}" ${v.name === 'pasqual' ? 'selected' : ''}>${v.name}</option>`
    ).join('');
}

function populateLanguageSelect() {
    elements.languageSelect.innerHTML = state.languages.map(l =>
        `<option value="${l}" ${l === 'fr' ? 'selected' : ''}>${l.toUpperCase()}</option>`
    ).join('');
}

function populateVoiceChips() {
    elements.voiceChips.innerHTML = state.voices.map(v => `
        <div class="voice-chip ${v.name === elements.voiceSelect.value ? 'active' : ''}" data-voice="${v.name}">
            <span>${v.name}</span>
            <button class="preview-btn" data-voice="${v.name}" title="Prévisualiser">🔊</button>
        </div>
    `).join('');
}

function updateEngineParams() {
    const engine = elements.engineSelect.value;
    const xttsParams = document.querySelectorAll('.param-xtts');
    const fishParams = document.querySelectorAll('.param-fish');

    if (engine === 'xtts_v2') {
        xttsParams.forEach(el => el.style.display = 'flex');
        fishParams.forEach(el => el.style.display = 'none');
    } else {
        xttsParams.forEach(el => el.style.display = 'none');
        fishParams.forEach(el => el.style.display = 'flex');
    }
}

function updateVoicePresets(voiceName) {
    const voice = state.voices.find(v => v.name === voiceName);
    if (voice) {
        elements.tempSlider.value = voice.temperature || 0.75;
        elements.tempValue.textContent = (voice.temperature || 0.75).toFixed(2);
        elements.speedSlider.value = voice.speed || 1.0;
        elements.speedValue.textContent = (voice.speed || 1.0).toFixed(1);
    }
}

// =============================================================================
// Timeline Functions
// =============================================================================

function ensureTrack(voiceName) {
    if (!state.tracks[voiceName]) {
        state.tracks[voiceName] = {
            samples: [],
            muted: false,
            solo: false
        };
    }
    return state.tracks[voiceName];
}

function addSampleToTrack(sampleData) {
    const track = ensureTrack(sampleData.voice);

    // Calculate start time (end of last sample on this track + 0.3s gap)
    let startTime = 0;
    if (track.samples.length > 0) {
        const lastSample = track.samples[track.samples.length - 1];
        startTime = lastSample.startTime + lastSample.duration + 0.3;
    }

    const sample = {
        ...sampleData,
        startTime,
        volume: 1.0,
        trimStart: 0,
        trimEnd: sampleData.duration
    };

    track.samples.push(sample);
    state.samples.push(sample);

    renderTimeline();
    updateTimelineInfo();
}

function removeSample(sampleId) {
    // Find and remove from track
    for (const voiceName in state.tracks) {
        const track = state.tracks[voiceName];
        const idx = track.samples.findIndex(s => s.id === sampleId);
        if (idx !== -1) {
            const sample = track.samples[idx];
            track.samples.splice(idx, 1);
            deleteSampleAPI(sample.filename);
            break;
        }
    }

    // Remove from flat list
    state.samples = state.samples.filter(s => s.id !== sampleId);

    renderTimeline();
    updateTimelineInfo();
}

function getTotalDuration() {
    let maxEnd = 0;
    for (const sample of state.samples) {
        const end = sample.startTime + sample.duration;
        if (end > maxEnd) maxEnd = end;
    }
    return maxEnd;
}

function getAllSamplesForExport() {
    return state.samples.map(s => ({
        filename: s.filename,
        path: s.path,
        voice: s.voice,
        start_time: s.startTime,
        duration: s.duration,
        volume: s.volume
    }));
}

function updateTimelineInfo() {
    const duration = getTotalDuration();
    elements.totalDuration.textContent = duration.toFixed(1) + 's';
    elements.sampleCount.textContent = state.samples.length;
    elements.emptyState.style.display = state.samples.length === 0 ? 'flex' : 'none';
}

// =============================================================================
// Timeline Rendering
// =============================================================================

function renderTimeline() {
    const trackNames = Object.keys(state.tracks).filter(name => state.tracks[name].samples.length > 0);

    if (trackNames.length === 0) {
        elements.tracksContainer.innerHTML = '<div class="playhead-line" id="playheadLine"></div>';
        return;
    }

    const totalDuration = Math.max(getTotalDuration() + 2, 10);

    // Render time ruler
    renderTimeRuler(totalDuration);

    // Render tracks
    let html = '<div class="playhead-line" id="playheadLine"></div>';
    html += trackNames.map(voiceName => {
        const track = state.tracks[voiceName];
        return `
            <div class="track" data-voice="${voiceName}">
                <div class="track-header">
                    <div class="track-name">
                        <span>${voiceName}</span>
                    </div>
                    <div class="track-controls">
                        <button class="track-btn ${track.muted ? 'active' : ''}" data-action="mute" data-voice="${voiceName}">M</button>
                        <button class="track-btn ${track.solo ? 'active' : ''}" data-action="solo" data-voice="${voiceName}">S</button>
                    </div>
                </div>
                <div class="track-content" data-voice="${voiceName}" style="width: ${totalDuration * state.zoom}px;">
                    ${track.samples.map(sample => renderSample(sample)).join('')}
                </div>
            </div>
        `;
    }).join('');

    elements.tracksContainer.innerHTML = html;

    // Re-get playhead reference
    elements.playheadLine = document.getElementById('playheadLine');

    // Add event listeners to samples
    attachSampleEventListeners();
}

function renderTimeRuler(totalDuration) {
    const tickInterval = state.zoom >= 80 ? 1 : state.zoom >= 40 ? 2 : 5;
    let html = '<div class="playhead-marker" id="playheadMarker"></div>';

    for (let t = 0; t <= totalDuration; t += tickInterval) {
        const x = t * state.zoom;
        html += `<div class="time-tick" style="left: ${x}px">${t}s</div>`;
    }

    elements.timeRuler.innerHTML = html;
    elements.timeRuler.style.width = (totalDuration * state.zoom) + 'px';

    // Re-get playhead marker reference
    elements.playheadMarker = document.getElementById('playheadMarker');
}

function renderSample(sample) {
    const left = sample.startTime * state.zoom;
    const width = Math.max(sample.duration * state.zoom, 40);
    const isSelected = state.selectedSample === sample.id;
    const engineBadge = sample.engine === 'fish_speech' ? '<span class="engine-badge fish">FS</span>' : '';

    return `
        <div class="sample ${isSelected ? 'selected' : ''}"
             data-id="${sample.id}"
             style="left: ${left}px; width: ${width}px;">
            <div class="sample-handle left"></div>
            <div class="sample-waveform">
                <canvas data-waveform='${JSON.stringify(sample.waveform || [])}'></canvas>
            </div>
            <div class="sample-label">${sample.text}${engineBadge}</div>
            <div class="sample-handle right"></div>
        </div>
    `;
}

function drawWaveforms() {
    document.querySelectorAll('.sample-waveform canvas').forEach(canvas => {
        const waveformData = JSON.parse(canvas.dataset.waveform || '[]');
        const ctx = canvas.getContext('2d');

        // Set canvas size
        canvas.width = canvas.offsetWidth * 2;
        canvas.height = canvas.offsetHeight * 2;
        ctx.scale(2, 2);

        const width = canvas.offsetWidth;
        const height = canvas.offsetHeight;
        const centerY = height / 2;

        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';

        const barWidth = waveformData.length > 0 ? width / waveformData.length : 1;

        waveformData.forEach((amplitude, i) => {
            const barHeight = Math.max(2, amplitude * height * 0.8);
            const x = i * barWidth;
            const y = centerY - barHeight / 2;
            ctx.fillRect(x, y, Math.max(1, barWidth - 1), barHeight);
        });
    });
}

// =============================================================================
// Playhead Animation
// =============================================================================

function updatePlayhead(time) {
    const x = time * state.zoom;
    elements.playheadTime.textContent = time.toFixed(1) + 's';

    if (elements.playheadLine) {
        elements.playheadLine.style.left = (120 + x) + 'px';  // 120px is track header width
        elements.playheadLine.classList.add('active');
    }

    if (elements.playheadMarker) {
        elements.playheadMarker.style.left = x + 'px';
        elements.playheadMarker.classList.add('active');
    }
}

function hidePlayhead() {
    elements.playheadTime.textContent = '0.0s';

    if (elements.playheadLine) {
        elements.playheadLine.classList.remove('active');
    }
    if (elements.playheadMarker) {
        elements.playheadMarker.classList.remove('active');
    }
}

// =============================================================================
// Drag & Drop
// =============================================================================

let dragState = {
    isDragging: false,
    sample: null,
    startX: 0,
    startLeft: 0,
    handle: null
};

function attachSampleEventListeners() {
    document.querySelectorAll('.sample').forEach(el => {
        el.addEventListener('mousedown', onSampleMouseDown);
        el.addEventListener('contextmenu', onSampleContextMenu);
        el.addEventListener('dblclick', onSampleDoubleClick);
    });

    document.querySelectorAll('.track-btn').forEach(el => {
        el.addEventListener('click', onTrackButtonClick);
    });

    // Draw waveforms after DOM is ready
    requestAnimationFrame(drawWaveforms);
}

function onSampleMouseDown(e) {
    const sampleEl = e.target.closest('.sample');
    if (!sampleEl) return;

    const sampleId = sampleEl.dataset.id;
    const sample = state.samples.find(s => s.id === sampleId);
    if (!sample) return;

    // Check if clicking on handle
    let handle = null;
    if (e.target.classList.contains('sample-handle')) {
        handle = e.target.classList.contains('left') ? 'left' : 'right';
    }

    // Select sample
    state.selectedSample = sampleId;
    document.querySelectorAll('.sample').forEach(el => el.classList.remove('selected'));
    sampleEl.classList.add('selected');

    // Start drag
    dragState = {
        isDragging: true,
        sample,
        sampleEl,
        startX: e.clientX,
        startLeft: sample.startTime * state.zoom,
        startWidth: sample.duration * state.zoom,
        startDuration: sample.duration,
        handle
    };

    sampleEl.classList.add('dragging');
    e.preventDefault();
}

function onMouseMove(e) {
    if (!dragState.isDragging) return;

    const deltaX = e.clientX - dragState.startX;

    if (dragState.handle === 'left') {
        const newLeft = Math.max(0, dragState.startLeft + deltaX);
        const newWidth = dragState.startWidth - deltaX;
        if (newWidth > 20) {
            dragState.sampleEl.style.left = newLeft + 'px';
            dragState.sampleEl.style.width = newWidth + 'px';
        }
    } else if (dragState.handle === 'right') {
        const newWidth = Math.max(20, dragState.startWidth + deltaX);
        dragState.sampleEl.style.width = newWidth + 'px';
    } else {
        const newLeft = Math.max(0, dragState.startLeft + deltaX);
        dragState.sampleEl.style.left = newLeft + 'px';
    }
}

async function onMouseUp(e) {
    if (!dragState.isDragging) return;

    const deltaX = e.clientX - dragState.startX;
    const deltaTime = deltaX / state.zoom;

    if (dragState.handle === 'left') {
        // Apply left trim - update duration
        const newStartTime = Math.max(0, dragState.sample.startTime + deltaTime);
        const newDuration = Math.max(0.1, dragState.startDuration - deltaTime);
        dragState.sample.startTime = newStartTime;
        dragState.sample.duration = newDuration;
        dragState.sample.trimStart = (dragState.sample.trimStart || 0) + deltaTime;

        // Fetch new waveform for trimmed sample
        await updateSampleWaveform(dragState.sample);

    } else if (dragState.handle === 'right') {
        // Apply right trim
        const newDuration = Math.max(0.1, dragState.startDuration + deltaTime);
        dragState.sample.duration = newDuration;

        // Fetch new waveform for trimmed sample
        await updateSampleWaveform(dragState.sample);

    } else {
        // Apply move
        const newLeft = Math.max(0, dragState.startLeft + deltaX);
        dragState.sample.startTime = newLeft / state.zoom;
    }

    dragState.sampleEl.classList.remove('dragging');
    dragState = { isDragging: false };

    renderTimeline();
    updateTimelineInfo();
}

async function updateSampleWaveform(sample) {
    // For now, just recalculate the waveform display based on trim
    // In a more advanced implementation, we would call the API to get trimmed audio waveform
    try {
        const data = await fetchWaveform(sample.filename);
        if (data && data.waveform) {
            sample.waveform = data.waveform;
        }
    } catch (err) {
        console.error('Failed to update waveform:', err);
    }
}

// =============================================================================
// Context Menu
// =============================================================================

let contextSampleId = null;

function onSampleContextMenu(e) {
    e.preventDefault();

    const sampleEl = e.target.closest('.sample');
    if (!sampleEl) return;

    contextSampleId = sampleEl.dataset.id;
    const sample = state.samples.find(s => s.id === contextSampleId);

    if (sample) {
        elements.volumeSlider.value = sample.volume;
        elements.volumeValue.textContent = Math.round(sample.volume * 100) + '%';
    }

    elements.contextMenu.style.left = e.clientX + 'px';
    elements.contextMenu.style.top = e.clientY + 'px';
    elements.contextMenu.classList.add('active');
}

function hideContextMenu() {
    elements.contextMenu.classList.remove('active');
    contextSampleId = null;
}

function onContextMenuAction(action) {
    if (!contextSampleId) return;

    const sample = state.samples.find(s => s.id === contextSampleId);
    if (!sample) return;

    switch (action) {
        case 'play':
            playSample(sample);
            break;
        case 'regenerate':
            regenerateSample(sample);
            break;
        case 'delete':
            removeSample(contextSampleId);
            break;
    }

    hideContextMenu();
}

function onSampleDoubleClick(e) {
    const sampleEl = e.target.closest('.sample');
    if (!sampleEl) return;

    const sampleId = sampleEl.dataset.id;
    const sample = state.samples.find(s => s.id === sampleId);
    if (sample) {
        playSample(sample);
    }
}

// =============================================================================
// Playback
// =============================================================================

function playSample(sample) {
    elements.audioPlayer.src = sample.path;
    elements.audioPlayer.volume = sample.volume;
    elements.audioPlayer.play();
}

async function playAll() {
    if (state.isPlaying) {
        stopPlayback();
        return;
    }

    if (state.samples.length === 0) return;

    state.isPlaying = true;
    elements.playIcon.textContent = '⏸';

    // Sort samples by start time
    const sortedSamples = [...state.samples].sort((a, b) => a.startTime - b.startTime);

    // Create audio context if needed
    if (!state.audioContext) {
        state.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }

    const ctx = state.audioContext;
    const startTime = ctx.currentTime;
    state.playStartTime = startTime;

    // Schedule all samples
    for (const sample of sortedSamples) {
        // Check if track is muted
        const track = state.tracks[sample.voice];
        if (track && track.muted) continue;

        // Check solo
        const hasSolo = Object.values(state.tracks).some(t => t.solo);
        if (hasSolo && track && !track.solo) continue;

        try {
            const response = await fetch(sample.path);
            const arrayBuffer = await response.arrayBuffer();
            const audioBuffer = await ctx.decodeAudioData(arrayBuffer);

            const source = ctx.createBufferSource();
            const gainNode = ctx.createGain();

            source.buffer = audioBuffer;
            gainNode.gain.value = sample.volume;

            source.connect(gainNode);
            gainNode.connect(ctx.destination);

            source.start(startTime + sample.startTime);
        } catch (err) {
            console.error('Error playing sample:', err);
        }
    }

    // Animate playhead
    const totalDuration = getTotalDuration();

    const animatePlayhead = () => {
        if (!state.isPlaying) return;

        const elapsed = state.audioContext.currentTime - state.playStartTime;
        updatePlayhead(elapsed);

        if (elapsed >= totalDuration) {
            stopPlayback();
            return;
        }

        state.playbackAnimationId = requestAnimationFrame(animatePlayhead);
    };

    animatePlayhead();
}

function stopPlayback() {
    state.isPlaying = false;
    elements.playIcon.textContent = '▶';

    if (state.playbackAnimationId) {
        cancelAnimationFrame(state.playbackAnimationId);
        state.playbackAnimationId = null;
    }

    hidePlayhead();

    if (state.audioContext) {
        state.audioContext.close();
        state.audioContext = null;
    }
}

async function regenerateSample(sample) {
    showLoading('Régénération...');

    try {
        const voice = state.voices.find(v => v.name === sample.voice);
        const engine = sample.engine || state.currentEngine;

        const params = engine === 'xtts_v2'
            ? { temperature: voice?.temperature || 0.75, speed: voice?.speed || 1.0 }
            : { temperature: 0.7, top_p: 0.7, repetition_penalty: 1.2 };

        const result = await generateSample(
            sample.text,
            sample.voice,
            engine,
            elements.languageSelect.value,
            params
        );

        // Replace old sample with new one at same position
        const newSample = {
            ...result.sample,
            startTime: sample.startTime,
            volume: sample.volume
        };

        // Remove old
        removeSample(sample.id);

        // Add new
        const track = ensureTrack(newSample.voice);
        track.samples.push(newSample);
        state.samples.push(newSample);

        renderTimeline();
        updateTimelineInfo();

    } catch (err) {
        alert('Erreur: ' + err.message);
    } finally {
        hideLoading();
    }
}

// =============================================================================
// Track Controls
// =============================================================================

function onTrackButtonClick(e) {
    const action = e.target.dataset.action;
    const voiceName = e.target.dataset.voice;
    const track = state.tracks[voiceName];

    if (!track) return;

    if (action === 'mute') {
        track.muted = !track.muted;
    } else if (action === 'solo') {
        track.solo = !track.solo;
    }

    renderTimeline();
}

// =============================================================================
// Event Handlers
// =============================================================================

async function onGenerate() {
    const text = elements.textInput.value.trim();
    if (!text) return;

    const voice = elements.voiceSelect.value;
    const engine = elements.engineSelect.value;
    const language = elements.languageSelect.value;

    // Get params based on engine
    let params;
    if (engine === 'xtts_v2') {
        params = {
            temperature: parseFloat(elements.tempSlider.value),
            speed: parseFloat(elements.speedSlider.value)
        };
    } else {
        params = {
            temperature: parseFloat(elements.fishTempSlider.value),
            top_p: parseFloat(elements.topPSlider.value),
            repetition_penalty: parseFloat(elements.repPenaltySlider.value)
        };
    }

    showLoading('Génération en cours...');
    elements.generateBtn.disabled = true;

    try {
        const result = await generateSample(text, voice, engine, language, params);
        addSampleToTrack(result.sample);
        elements.textInput.value = '';
        elements.textInput.focus();
    } catch (err) {
        alert('Erreur: ' + err.message);
    } finally {
        hideLoading();
        elements.generateBtn.disabled = false;
    }
}

async function onEngineChange() {
    const engine = elements.engineSelect.value;
    await selectEngine(engine);
    updateEngineParams();
    populateLanguageSelect();
}

async function onUploadVoice() {
    const name = elements.voiceNameInput.value.trim();
    const file = elements.voiceFileInput.files[0];

    if (!name || !file) {
        alert('Veuillez remplir tous les champs');
        return;
    }

    showLoading('Upload...');

    try {
        await uploadVoice(name, file);
        await fetchVoices();
        populateVoiceSelect();
        populateVoiceChips();
        closeUploadModal();
    } catch (err) {
        alert('Erreur: ' + err.message);
    } finally {
        hideLoading();
    }
}

function openUploadModal() {
    elements.voiceNameInput.value = '';
    elements.voiceFileInput.value = '';
    elements.uploadModal.classList.add('active');
}

function closeUploadModal() {
    elements.uploadModal.classList.remove('active');
}

// =============================================================================
// Initialization
// =============================================================================

async function init() {
    updateStatus('Chargement...', true);

    try {
        // Fetch engines and voices
        await fetchEngines();
        await fetchVoices();

        // Populate UI
        populateEngineSelect();
        populateVoiceSelect();
        populateLanguageSelect();
        populateVoiceChips();
        updateVoicePresets('pasqual');
        updateEngineParams();

        const engineInfo = state.engines.find(e => e.name === state.currentEngine);
        const device = engineInfo?.available ? 'Ready' : 'Not loaded';
        updateStatus(`${state.currentEngine} - ${device}`, false);

    } catch (err) {
        updateStatus('Erreur de connexion', false);
        console.error(err);
    }

    // Event listeners
    elements.generateBtn.addEventListener('click', onGenerate);
    elements.textInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') onGenerate();
    });

    elements.engineSelect.addEventListener('change', onEngineChange);

    elements.voiceSelect.addEventListener('change', e => {
        updateVoicePresets(e.target.value);
        populateVoiceChips();
    });

    // XTTS sliders
    elements.tempSlider.addEventListener('input', e => {
        elements.tempValue.textContent = parseFloat(e.target.value).toFixed(2);
    });
    elements.speedSlider.addEventListener('input', e => {
        elements.speedValue.textContent = parseFloat(e.target.value).toFixed(1);
    });

    // Fish Speech sliders
    elements.fishTempSlider.addEventListener('input', e => {
        elements.fishTempValue.textContent = parseFloat(e.target.value).toFixed(2);
    });
    elements.topPSlider.addEventListener('input', e => {
        elements.topPValue.textContent = parseFloat(e.target.value).toFixed(2);
    });
    elements.repPenaltySlider.addEventListener('input', e => {
        elements.repPenaltyValue.textContent = parseFloat(e.target.value).toFixed(1);
    });

    elements.zoomSlider.addEventListener('input', e => {
        state.zoom = parseInt(e.target.value);
        renderTimeline();
    });

    // Voice chips
    elements.voiceChips.addEventListener('click', e => {
        const chip = e.target.closest('.voice-chip');
        const previewBtn = e.target.closest('.preview-btn');

        if (previewBtn) {
            previewVoice(previewBtn.dataset.voice);
            return;
        }

        if (chip) {
            elements.voiceSelect.value = chip.dataset.voice;
            updateVoicePresets(chip.dataset.voice);
            populateVoiceChips();
        }
    });

    // Upload modal
    elements.uploadVoiceBtn.addEventListener('click', openUploadModal);
    elements.cancelUploadBtn.addEventListener('click', closeUploadModal);
    elements.confirmUploadBtn.addEventListener('click', onUploadVoice);

    // Playback
    elements.playBtn.addEventListener('click', playAll);
    elements.stopBtn.addEventListener('click', stopPlayback);

    // Export
    elements.exportWavBtn.addEventListener('click', () => exportTimeline('wav'));
    elements.exportZipBtn.addEventListener('click', () => exportTimeline('zip'));
    elements.exportEdlBtn.addEventListener('click', () => exportTimeline('edl'));

    // Context menu
    elements.contextMenu.addEventListener('click', e => {
        const item = e.target.closest('.context-menu-item');
        if (item) {
            onContextMenuAction(item.dataset.action);
        }
    });

    elements.volumeSlider.addEventListener('input', e => {
        const volume = parseFloat(e.target.value);
        elements.volumeValue.textContent = Math.round(volume * 100) + '%';

        if (contextSampleId) {
            const sample = state.samples.find(s => s.id === contextSampleId);
            if (sample) sample.volume = volume;
        }
    });

    document.addEventListener('click', e => {
        if (!elements.contextMenu.contains(e.target)) {
            hideContextMenu();
        }
    });

    // Global drag handlers
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);

    // Initial render
    updateTimelineInfo();
}

// Start
init();
