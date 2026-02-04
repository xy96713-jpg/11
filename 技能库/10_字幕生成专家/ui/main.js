document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const resultView = document.getElementById('result-view');
    const progressFill = document.querySelector('.progress-fill');
    const thresholdSlider = document.getElementById('threshold-slider');
    const thresholdDisplay = document.getElementById('threshold-display');

    if (thresholdSlider) {
        thresholdSlider.addEventListener('input', (e) => {
            thresholdDisplay.textContent = `${e.target.value}% (${e.target.value > 90 ? '极高精度' : '普通精度'})`;
        });
    }

    // UI steps
    const stepSeparation = document.getElementById('step-separation');
    const stepTranscription = document.getElementById('step-transcription');
    const stepSrt = document.getElementById('step-srt');

    if (dropZone) {
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
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) handleFile(e.target.files[0]);
        });
    }

    function handleFile(file) {
        console.log('Processing file:', file.name);
        startSimulation();
    }

    function startSimulation() {
        // Reset
        if (progressFill) progressFill.style.width = '0%';
        [stepSeparation, stepTranscription, stepSrt].forEach(s => {
            if (s) s.classList.remove('active');
        });
        if (resultView) resultView.style.display = 'none';

        // Step 1: Separation
        setTimeout(() => {
            if (stepSeparation) stepSeparation.classList.add('active');
            if (progressFill) progressFill.style.width = '30%';
        }, 500);

        // Step 2: Transcription
        setTimeout(() => {
            if (stepTranscription) stepTranscription.classList.add('active');
            if (progressFill) progressFill.style.width = '70%';
        }, 3000);

        // Step 3: SRT
        setTimeout(() => {
            if (stepSrt) stepSrt.classList.add('active');
            if (progressFill) progressFill.style.width = '100%';
            showResults();
        }, 5500);
    }

    function showResults() {
        if (resultView) resultView.style.display = 'block';
        const srtContent = document.getElementById('srt-content');
        if (srtContent) {
            srtContent.textContent = `1
00:00:01,240 --> 00:00:04,300
(XG - HYPNOTIZE)
Hey, you're running from what you can't escape.

2
00:00:04,800 --> 00:00:07,500
(NewJeans - Super Shy)
I'm super shy, super shy

3
00:00:08,100 --> 00:00:11,400
(Mashup Overlap - Context Guided)
But wait a minute while I make you mine.`;
        }

        if (resultView) resultView.scrollIntoView({ behavior: 'smooth' });
    }
});
