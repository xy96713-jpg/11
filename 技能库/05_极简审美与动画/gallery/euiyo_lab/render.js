/**
 * euiyo Retro-Glitch Renderer
 * Inherits: Skill 00 (Decision) & Skill 09 (Calculation)
 */

const canvas = document.getElementById('glitchCanvas');
const ctx = canvas.getContext('2d', { alpha: false });

let width, height;
let frame = 0;
let glitchTimer = 0;

// Config (Computational Logic)
const CONFIG = {
    scanlineDensity: 3,
    baseColor: 'rgb(100, 200, 100)',
    accentColor: 'rgb(200, 255, 100)',
    fontSize: 220, // Increased for VT323
    text: 'euiyo',
    subtext: 'VIDEO',
    fontMain: 'VT323',
    fontSub: 'Space Grotesk'
};

function resize() {
    width = canvas.width = 1200;
    height = canvas.height = 800;
    ctx.imageSmoothingEnabled = false;
}

function drawBackground() {
    ctx.fillStyle = '#050a05';
    ctx.fillRect(0, 0, width, height);

    // Subtle rhythmic glow (Phase 4.1)
    const glow = Math.sin(frame * 0.05) * 5 + 10;
    ctx.shadowBlur = glow;
    ctx.shadowColor = CONFIG.baseColor;
}

function drawText(offsetX = 0, color = CONFIG.baseColor) {
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Main Text (Pixel Branding - Skill 05 Core)
    ctx.font = `${CONFIG.fontSize}px ${CONFIG.fontMain}`;
    ctx.fillStyle = color;
    ctx.fillText(CONFIG.text, width / 2 + offsetX, height / 2 - 40);

    // Subtext (Technical Grotesk)
    ctx.font = `bold 32px ${CONFIG.fontSub}`;
    ctx.letterSpacing = "15px"; // Character tracking (Experimental CSS Prop)
    const metrics = ctx.measureText(CONFIG.subtext);
    const boxW = metrics.width + 100;

    // Draw hollow box
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.strokeRect(width / 2 - boxW / 2 + offsetX, height / 2 + 50, boxW, 50);

    ctx.fillStyle = color;
    ctx.fillText(CONFIG.subtext, width / 2 + offsetX + 7.5, height / 2 + 77); // Half letter-spacing offset
    ctx.letterSpacing = "0px";
}

function applyScanlines() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
    for (let y = 0; y < height; y += CONFIG.scanlineDensity) {
        ctx.fillRect(0, y, width, 1);
    }
}

function applyGlitch() {
    if (glitchTimer > 0) {
        // Pixel Shift (Skill 09: Logic Partition)
        const shiftY = Math.random() * height;
        const h = Math.random() * 50 + 10;
        const destX = (Math.random() - 0.5) * 30;

        ctx.drawImage(canvas, 0, shiftY, width, h, destX, shiftY, width, h);

        // Chromatic Aberration Simulation
        if (Math.random() > 0.8) {
            ctx.globalCompositeOperation = 'screen';
            drawText(-5, 'rgba(255, 0, 0, 0.3)');
            drawText(5, 'rgba(0, 255, 255, 0.3)');
            ctx.globalCompositeOperation = 'source-over';
        }

        glitchTimer--;
    }

    // Trigger random glitches
    if (Math.random() > 0.98) {
        glitchTimer = Math.floor(Math.random() * 10) + 2;
    }
}

function render() {
    frame++;
    drawBackground();

    // Draw base text
    drawText();

    // Apply physical effects
    applyScanlines();
    applyGlitch();

    // Final Phosphor Bloom
    ctx.globalAlpha = 0.05;
    ctx.fillStyle = CONFIG.accentColor;
    ctx.fillRect(0, 0, width, height);
    ctx.globalAlpha = 1.0;

    requestAnimationFrame(render);
}

window.addEventListener('resize', resize);
resize();

// Wait for fonts to load before rendering (Skill 09 Audit Constraint)
document.fonts.ready.then(() => {
    console.log("Fonts loaded. Initializing render loop...");
    render();
});
