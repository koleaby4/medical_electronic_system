document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('startRecordingBtn');
    const pauseBtn = document.getElementById('pauseRecordingBtn');
    const finishBtn = document.getElementById('finishRecordingBtn');
    const recordingsList = document.getElementById('recordingsList');
    const recordingIndicator = document.getElementById('recordingIndicator');

    let mediaRecorder;
    let audioChunks = [];
    let recordings = []; // Store blobs and their IDs

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error('MediaDevices API not supported');
        if (startBtn) startBtn.disabled = true;
        return;
    }

    startBtn.onclick = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm;codecs=opus' });
                const id = Date.now();
                recordings.push({ id, blob: audioBlob });
                addRecordingToList(audioBlob, id);
                audioChunks = [];
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            updateUI('recording');
        } catch (err) {
            console.error('Error starting recording:', err);
            alert('Could not start recording. Please check microphone permissions.');
        }
    };

    pauseBtn.onclick = () => {
        if (mediaRecorder.state === 'recording') {
            mediaRecorder.pause();
            updateUI('paused');
        } else if (mediaRecorder.state === 'paused') {
            mediaRecorder.resume();
            updateUI('recording');
        }
    };

    finishBtn.onclick = () => {
        mediaRecorder.stop();
        updateUI('idle');
    };

    function updateUI(state) {
        if (state === 'recording') {
            startBtn.classList.add('d-none');
            pauseBtn.classList.remove('d-none');
            pauseBtn.innerText = 'Pause';
            finishBtn.classList.remove('d-none');
            recordingIndicator.classList.remove('d-none');
            recordingIndicator.innerText = 'Recording...';
        } else if (state === 'paused') {
            pauseBtn.innerText = 'Resume';
            recordingIndicator.innerText = 'Paused';
        } else if (state === 'idle') {
            startBtn.classList.remove('d-none');
            pauseBtn.classList.add('d-none');
            finishBtn.classList.add('d-none');
            recordingIndicator.classList.add('d-none');
        }
    }

    function addRecordingToList(blob, id) {
        const url = URL.createObjectURL(blob);
        
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex align-items-center justify-content-between';
        li.id = `recording-item-${id}`;

        const audio = document.createElement('audio');
        audio.controls = true;
        audio.src = url;
        audio.className = 'me-2 flex-grow-1';
        audio.style.maxHeight = '35px';

        const deleteBtn = document.createElement('button');
        deleteBtn.type = 'button';
        deleteBtn.className = 'btn btn-outline-danger btn-sm';
        deleteBtn.innerHTML = '&times;';
        deleteBtn.onclick = () => {
            li.remove();
            recordings = recordings.filter(r => r.id !== id);
        };

        li.appendChild(audio);
        li.appendChild(deleteBtn);
        recordingsList.appendChild(li);
    }

    // Intercept HTMX before request to add recordings
    document.body.addEventListener('htmx:configRequest', (event) => {
        if (event.detail.elt.id === 'medicalCheckForm') {
            recordings.forEach((r, index) => {
                const file = new File([r.blob], `recording_${index}.webm`, { type: 'audio/webm;codecs=opus' });
                if (!event.detail.parameters[`voice_recordings`]) {
                    event.detail.parameters[`voice_recordings`] = file;
                } else {
                    if (!Array.isArray(event.detail.parameters[`voice_recordings`])) {
                        event.detail.parameters[`voice_recordings`] = [event.detail.parameters[`voice_recordings`]];
                    }
                    event.detail.parameters[`voice_recordings`].push(file);
                }
            });
        }
    });
});
