document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const resultView = document.getElementById('result-view');
    const progressFill = document.querySelector('.progress-fill');
    
    // UI steps
    const stepSeparation = document.getElementById('step-separation');
    const stepTranscription = document.getElementById('step-transcription');
    const stepSrt = document.getElementById('step-srt');

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--accent)';
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = 'rgba(255, 255, 255, 0.1)';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        const files = e.dataTransfer.files;
        if (files.length > 0) handleFile(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFile(e.target.files[0]);
    });

    function handleFile(file) {
        console.log('Processing file:', file.name);
        startSimulation();
    }

    function startSimulation() {
        // Reset
        progressFill.style.width = '0%';
        [stepSeparation, stepTranscription, stepSrt].forEach(s => s.classList.remove('active'));
        resultView.style.display = 'none';

        // Step 1: Separation
        setTimeout(() => {
            stepSeparation.classList.add('active');
            progressFill.style.width = '30%';
        }, 500);

        // Step 2: Transcription
        setTimeout(() => {
            stepTranscription.classList.add('active');
            progressFill.style.width = '70%';
        }, 3000);

        // Step 3: SRT
        setTimeout(() => {
            stepSrt.classList.add('active');
            progressFill.style.width = '100%';
            showResults();
        }, 5500);
    }

    function showResults() {
        resultView.style.display = 'block';
        const srtContent = document.getElementById('srt-content');
        srtContent.textContent = `1
00:00:01,240 --> 00:00:04,500
(Upbeat Intro Music)

2
00:00:05,100 --> 00:00:08,200
Welcome to the 2026 Antigravity Lab.

3
00:00:08,450 --> 00:00:12,100
Everything flows like liquid glass.`;
        
        resultView.scrollIntoView({ behavior: 'smooth' });
    }
});
