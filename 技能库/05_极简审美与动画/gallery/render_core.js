/**
 * Studio 3.2 Rendering Core
 * Supports Multi-Modal Effects (Mesh, Gravity, Retro, Glitch)
 * Supports both Mini-Card Previews and Full-Screen Viewer
 */

const RenderCore = {
    // Shared State for all renderers
    time: 0,

    init: () => {
        requestAnimationFrame(RenderCore.loop);
        RenderCore.initMiniCards();
        RenderCore.setupGlobalListeners();
    },

    setupGlobalListeners: () => {
        // Dynamic Re-scale: 防止窗口缩放导致的模糊
        window.addEventListener('resize', () => {
            RenderCore.renderers.forEach(r => {
                if (r.canvas) {
                    const rect = r.canvas.parentElement.getBoundingClientRect();
                    r.canvas.width = rect.width;
                    r.canvas.height = rect.height;
                    r.width = rect.width;
                    r.height = rect.height;
                }
            });
            // Also resize viewer if active
            if (window.viewerCanvas) {
                window.viewerCanvas.width = window.innerWidth;
                window.viewerCanvas.height = window.innerHeight;
            }
        });
    },

    loop: (timestamp) => {
        // Delta Time Calculation (144Hz 适配)
        if (!RenderCore.lastTime) RenderCore.lastTime = timestamp;
        const deltaTime = (timestamp - RenderCore.lastTime) / 1000;
        RenderCore.lastTime = timestamp;

        RenderCore.time += deltaTime;

        // Condition 1: 全局渲染互斥 (当全屏预览激活时，挂起后台 mini-cards)
        const isViewerActive = window.viewerActive && window.viewerRenderer;

        if (!isViewerActive) {
            // Render all active AND visible mini-canvases
            RenderCore.renderers.forEach(r => {
                if (r.active && r.inView && r.ctx) {
                    // Skill 09 Anti-Magic: 使用逻辑时间而非简单累加，确保不同帧率一致性
                    r.render(r.ctx, r.width, r.height, RenderCore.time, false);
                }
            });
        }

        // Render full viewer if active
        if (isViewerActive) {
            const ctx = window.viewerCtx;
            const width = window.viewerCanvas.width;
            const height = window.viewerCanvas.height;
            ctx.fillStyle = '#020202';
            ctx.fillRect(0, 0, width, height);
            window.viewerRenderer(ctx, width, height, RenderCore.time, true);
        }

        requestAnimationFrame(RenderCore.loop);
    },

    renderers: [],

    initMiniCards: () => {
        const effects = [
            { id: 'canvas-mesh', type: 'mesh' },
            { id: 'canvas-gravity', type: 'gravity' },
            { id: 'canvas-retro', type: 'retro' },
            { id: 'canvas-glitch', type: 'glitch' },
            { id: 'canvas-city', type: 'city-lite' },
            { id: 'canvas-nj', type: 'nj-lite' },
            { id: 'canvas-nuclear', type: 'nuclear-lite' }
        ];

        // Intersection Observer: 视口可见性审计
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const renderer = RenderCore.renderers.find(r => r.canvas === entry.target);
                if (renderer) {
                    renderer.inView = entry.isIntersecting;
                    // console.log(`Card ${renderer.id} visibility: ${entry.isIntersecting}`);
                }
            });
        }, { threshold: 0.1 });

        effects.forEach(e => {
            const canvas = document.getElementById(e.id);
            if (canvas) {
                const rect = canvas.parentElement.getBoundingClientRect();
                canvas.width = rect.width;
                canvas.height = rect.height;

                const renderer = {
                    id: e.id,
                    active: true,
                    inView: false, // 初始不可见，等待 Observer 激活
                    canvas: canvas,
                    ctx: canvas.getContext('2d'),
                    width: canvas.width,
                    height: canvas.height,
                    render: RenderAlgorithms[e.type]
                };

                RenderCore.renderers.push(renderer);
                observer.observe(canvas);
            }
        });
    }
};

const RenderAlgorithms = {
    // 1. Fluid Mesh (Enhanced Harmonic Sine Summation)
    mesh: (ctx, w, h, time, isFull) => {
        const speed = isFull ? (state.speed / 50) : 0.6;
        const color = isFull ? state.color : '#00f3ff';
        const intensity = isFull ? (state.intensity / 50) : 0.5;

        // Skill 07 Math: 使用双缓冲清除，避免全屏重绘闪烁（如果需要），这里简化为透明度擦除以制造拖尾
        // ctx.clearRect(0,0,w,h); 
        // 使用 "Fade Effect" 模拟视觉暂留
        ctx.fillStyle = isFull ? 'rgba(2,2,2,0.2)' : '#020202';
        if (isFull) ctx.fillRect(0, 0, w, h);
        else ctx.clearRect(0, 0, w, h);

        ctx.strokeStyle = color;
        ctx.lineWidth = isFull ? 2 : 1.5;

        const lines = isFull ? 3 : 5;
        // Math: f(x, t) = A1*sin(w1*x + t) + A2*cos(w2*x + t)
        // 通过叠加不同频率的正弦波，模拟非周期性的“自然流体”
        for (let j = 0; j < lines; j++) {
            ctx.beginPath();
            const phaseOffset = j * (Math.PI / lines);
            const amplitudeBase = (isFull ? 60 : 25) * intensity;

            for (let i = 0; i <= w; i += 5) {
                // Harmonic Summation (谐波叠加)
                const wave1 = Math.sin(i * 0.003 + time * speed + phaseOffset);
                const wave2 = Math.cos(i * 0.01 + time * speed * 1.5);
                const y = (wave1 + wave2 * 0.5) * amplitudeBase + h / 2;

                if (i === 0) ctx.moveTo(i, y);
                else ctx.lineTo(i, y);
            }
            ctx.globalAlpha = 1 - (j / lines); // Depth fading
            ctx.stroke();
            ctx.globalAlpha = 1.0;
        }
    },

    // 2. Gravity Field (Newtonian Approximation)
    gravity: (ctx, w, h, time, isFull) => {
        const count = isFull ? 120 : 40;
        const color = isFull ? state.color : '#7000ff';

        if (isFull) {
            ctx.fillStyle = 'rgba(2,2,2,0.15)'; // Motion blur trail
            ctx.fillRect(0, 0, w, h);
        } else {
            ctx.clearRect(0, 0, w, h);
        }

        ctx.fillStyle = color;

        // Math: Particle Logic with Pseudo-Lissajous figures (李萨如图形模拟)
        for (let i = 0; i < count; i++) {
            // 使用素数乘数避免周期共振
            const t = time * 0.5;
            const seed = i * 137.5; // Golden angle

            // X: Simple Harmonic Motion
            // Y: Accelerated Motion Simulation
            const x = (Math.sin(seed + t * 0.3) * 0.4 + 0.5) * w;
            const y = (Math.cos(seed * 0.7 + t * 0.5) * 0.4 + 0.5) * h;

            // Size breathing function: sin^2(t) -> always positive
            const sizeBase = Math.sin(t * 2 + i);
            const size = (sizeBase * sizeBase) * (isFull ? 4 : 2.5);

            ctx.beginPath();
            ctx.arc(x, y, size, 0, Math.PI * 2);
            ctx.fill();
        }
    },

    // 3. Retro Grid
    retro: (ctx, w, h, time, isFull) => {
        const color = '#bd00ff';
        if (!isFull) ctx.clearRect(0, 0, w, h);

        ctx.strokeStyle = color;
        ctx.lineWidth = 1;

        // Perspective lines
        const cx = w / 2;
        const cy = h / 2;

        ctx.beginPath();
        for (let i = -10; i <= 10; i++) {
            ctx.moveTo(cx, cy);
            ctx.lineTo(cx + i * w * 0.5, h);
        }

        // Moving horizontal lines
        const speed = 200;
        const offset = (time * speed) % 100;
        for (let y = cy; y < h; y += 20) {
            const yPos = y + (offset * (y - cy) / h); // simple perspective fake
            if (yPos > h) continue;
            ctx.moveTo(0, yPos);
            ctx.lineTo(w, yPos);
        }
        ctx.stroke();
    },

    // 5. City Lite (LOD 0 for CityFlow)
    'city-lite': (ctx, w, h, time, isFull) => {
        if (!isFull) {
            ctx.fillStyle = '#101018'; // Dark city bg
            ctx.fillRect(0, 0, w, h);
        }

        // Neon Lines flowing
        const count = 15;
        ctx.lineWidth = 2;

        for (let i = 0; i < count; i++) {
            const y = (h / count) * i + Math.sin(time + i) * 10;
            const speed = (i % 2 === 0 ? 100 : -100) * ((i + 1) / count);
            const x = (time * speed) % w;
            const finalX = x < 0 ? x + w : x;

            // Neon Gradient
            const gradient = ctx.createLinearGradient(finalX, y, finalX + 100, y);
            gradient.addColorStop(0, 'rgba(0, 243, 255, 0)');
            gradient.addColorStop(0.5, i % 3 === 0 ? '#ff0055' : '#00f3ff'); // Cyberpunk Colors
            gradient.addColorStop(1, 'rgba(0, 243, 255, 0)');

            ctx.strokeStyle = gradient;
            ctx.beginPath();
            ctx.moveTo(finalX, y);
            ctx.lineTo(finalX + 80, y); // Trail length
            ctx.stroke();
        }
    },

    // 6. NJ Lite (LOD 0 for NewJeans Attributes)
    'nj-lite': (ctx, w, h, time, isFull) => {
        if (!isFull) {
            ctx.clearRect(0, 0, w, h);
        }

        // Sparkles (Blinking Stars)
        const count = 20;

        for (let i = 0; i < count; i++) {
            // Deterministic Randomness based on index
            const seed = i * 123.45;
            const x = (Math.sin(seed) * 0.5 + 0.5) * w;
            const y = (Math.cos(seed * 0.9) * 0.5 + 0.5) * h;

            // Twinkle Logic
            const twinkle = Math.sin(time * 3 + seed); // -1 to 1
            const alpha = Math.max(0, twinkle);

            if (alpha > 0.01) {
                ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
                ctx.beginPath();
                // Draw Star shape (simplified as diamond)
                const size = 3 * alpha;
                ctx.moveTo(x, y - size);
                ctx.lineTo(x + size, y);
                ctx.lineTo(x, y + size);
                ctx.lineTo(x - size, y);
                ctx.fill();
            }
        }
    },

    // 7. Nuclear Lite (LOD 0 for Nuclear Core)
    'nuclear-lite': (ctx, w, h, time, isFull) => {
        if (!isFull) {
            ctx.fillStyle = 'rgba(20, 0, 0, 0.2)'; // Slow trail
            ctx.fillRect(0, 0, w, h);
        }

        const cx = w / 2;
        const cy = h / 2;

        // Pulsing Core
        const pulse = Math.sin(time * 5) * 0.5 + 0.5; // 0 to 1
        const radius = 20 + pulse * 10;

        // Core Glow
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius * 2);
        grad.addColorStop(0, '#ffcc00'); // Hot center
        grad.addColorStop(0.5, '#ff4e50'); // Red rim
        grad.addColorStop(1, 'rgba(255, 0, 0, 0)');

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(cx, cy, radius * 2, 0, Math.PI * 2);
        ctx.fill();

        // Electrons
        const electrons = 3;
        ctx.strokeStyle = '#ff4e50';
        ctx.lineWidth = 1;

        for (let i = 0; i < electrons; i++) {
            const rot = time * 2 + i * (Math.PI * 2 / electrons);
            const ex = cx + Math.cos(rot) * 40;
            const ey = cy + Math.sin(rot) * 40;

            ctx.beginPath();
            ctx.arc(ex, ey, 2, 0, Math.PI * 2);
            ctx.stroke(); // Hollow electrons
        }
    }
};

window.RenderCore = RenderCore;
window.RenderAlgorithms = RenderAlgorithms;
